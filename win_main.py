# -*- coding: utf-8 -*-
import logging
import time
# Form implementation generated from reading ui file 'gui.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.
from queue import Queue
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QFileDialog, QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, \
    QWidget, QMenu, QMessageBox
from PyQt5.QtCore import QThread, QObject, pyqtSignal, Qt
from openpyxl import Workbook

from sql_handler import SQLHandler
from steam import SteamAuth
from sda_code import generator_code
from steam_tools import regex_recently_dropped, regex_vac_status, regex_csgo_account_info, is_this_week_drop, \
    parse_datetime
from win_gui import Ui_task_MainWindow, Ui_login_MainWindow

g_accounts = []

class Worker(QThread, QObject):
    finished = pyqtSignal()
    update_table_item_request = pyqtSignal(int, int, str)
    get_table_item = pyqtSignal(int, int)
    log_message = pyqtSignal(str)  # 新的日志消息信号

    def __init__(self, account, row_index, parent=None):
        QThread.__init__(self, parent)
        QObject.__init__(self, parent)
        self.account = account
        self.password = None
        self.row_index = row_index
        self.acc = None
        self.sql_handler = None
        # 定义普通箱子的名称数组
        self.normal_boxes = [
            "梦魇武器箱",
            "千瓦武器箱",
            "反冲武器箱",
            "变革武器箱",
            "裂空武器箱",
        ]

    def set_acc(self):
        # self.acc 序列化
        session_str = self.acc.serialize()
        self.sql_handler.set_account_session(self.acc.username, session_str)

    def get_acc_from_db(self):
        session = self.sql_handler.get_account_session(self.account)
        if session:
            auth = SteamAuth(self.account, self.password)
            auth.deserialize(session)
            self.acc = auth
            return True
        return False

    def run(self):
        step = 0
        try:
            self.sql_handler = SQLHandler()
            if self.check_cache():
                self.update_table_item_request.emit(self.row_index, 1, '读取缓存中..')
                self.set_data_from_cache()
                self.sql_handler.conn.close()
            else:
                self.password = g_accounts[self.row_index][1]
                login_state = self.login_task(self.account, self.password, self.row_index)
                step += 1
                if login_state:
                    print(f'{self.account}---{self.password}---login_success')
                    inventory_status, inventory_data = self.inventory_task()
                    step += 1
                    vac_status, vac = self.vac_check_task()
                    step += 1
                    account_info_status, csgo_account = self.csgo_account_info_task()
                    step += 1
                    self.save_cache(inventory_data, vac, csgo_account)
                    step += 1
                    self.sql_handler.conn.close()
        except Exception as e:
            print(f"{self.account}在第{step}步出现异常")
            print(f'Exception in run: {e}')
        finally:
            self.finished.emit()

    def save_cache(self, inventory_data, vac, csgo_account):
        if not is_this_week_drop(inventory_data[0]['date']):
            self.log_message.emit(f"{self.account} 本周未掉落")
        # user_info 格式 (id, user_account, user_password, drop_time, drop_item, drop_num, vac_status, is_this_week_drop, rank, exp)
        self.sql_handler.insert_or_update(self.account,
                                          self.password,
                                          inventory_data[0]['date'],
                                          inventory_data[1]['item_name'] + ',' + inventory_data[0]['item_name'],
                                          2,
                                          vac,
                                          is_this_week_drop(inventory_data[0]['date']),
                                          csgo_account['rank'],
                                          csgo_account['exp'])

    def check_rare_drop(self, drop_item):
        if drop_item not in self.normal_boxes:
            self.log_message.emit(f"恭喜! {self.account} 检测到稀有掉落: {drop_item}")
        pass

    def check_cache(self):
        drop_time = self.sql_handler.get_drop_time(self.account)
        if not drop_time:
            return False
        if is_this_week_drop(drop_time):
            return True
        return False

    def set_data_from_cache(self):
        user_info = self.sql_handler.get_user_info(self.account)
        # user_info 格式 (id, user_account, user_password, drop_time, drop_item, drop_num, vac_status, is_this_week_drop, rank, exp)
        # 账号
        self.update_table_item_request.emit(self.row_index, 0, f"{user_info[1]}")
        # 登录状态
        self.update_table_item_request.emit(self.row_index, 1, '读取缓存')
        # 最近掉落
        self.update_table_item_request.emit(self.row_index, 2, f"{user_info[4]}")
        # 掉落日期
        self.update_table_item_request.emit(self.row_index, 3, f"{user_info[3]}")
        # VAC状态
        self.update_table_item_request.emit(self.row_index, 4, f"{user_info[6]}")
        # 是否是本周掉落
        self.update_table_item_request.emit(self.row_index, 5, f"{user_info[7]}")
        # 等级
        self.update_table_item_request.emit(self.row_index, 6, f"{user_info[8]}")
        # 当前经验
        self.update_table_item_request.emit(self.row_index, 7, f"{user_info[9]}")

        # 将 裂空武器箱,P250 | 沙丘之黄 分成两个
        drop_items = user_info[4].split(',')
        self.check_rare_drop(drop_items[0])

    def login_task(self, account, password, row_index):
        if self.get_acc_from_db() and self.acc.check_session():
            self.update_table_item_request.emit(row_index, 1, '登录成功')
            return True
        self.acc = SteamAuth(account, password)
        rsa_state, rsa_re = self.acc.get_rsa_public_key()
        # 休息1秒
        time.sleep(1)
        if rsa_state:
            encode_password = self.acc.rsa_encrypt(rsa_re.publickey_mod, rsa_re.publickey_exp)
            # 休息1秒
            time.sleep(1)
            send_state, send_re = self.acc.send_encode_request(encode_password, rsa_re.timestamp)
            # 休息1秒
            time.sleep(1)
            if send_state:
                print('获取验证码...')
                if len(send_re.allowed_confirmations) > 0:
                    if send_re.allowed_confirmations[0].confirmation_type == 2:
                        print('尝试获取邮箱令牌')
                        self.update_table_item_request.emit(row_index, 1, '尝试获取邮箱令牌')
                        pass
                    if send_re.allowed_confirmations[0].confirmation_type == 3:
                        print('尝试获取手机令牌')
                        self.update_table_item_request.emit(row_index, 1, '尝试获取手机令牌')
                        gen_state, code = generator_code(self.acc.steam_id, self.acc.username)
                        if gen_state:
                            print('获取验证码成功')
                            print(f'code: {code}')
                            state = self.acc.auth_code(code)
                            if state:
                                token_state = self.acc.get_token()
                                if token_state:
                                    self.set_acc()
                                    self.update_table_item_request.emit(row_index, 1, '登录成功')
                                    return True
                                else:
                                    self.update_table_item_request.emit(row_index, 1, '登陆失败')
                                    return False
                        else:
                            self.update_table_item_request.emit(row_index, 1, '获取验证码错误')
                            return False
            else:
                print('获取密钥失败')
                self.update_table_item_request.emit(row_index, 1, '登陆失败')
                return False
        else:
            self.update_table_item_request.emit(row_index, 1, '获取密钥失败')
            return False

    def csgo_account_info_task(self):
        self.update_table_item_request.emit(self.row_index, 1, '正在获取CSGO账户信息...')
        state, account_re = self.acc.get_csgo_account_info()
        if state:
            self.update_table_item_request.emit(self.row_index, 1, '获取CSGO账户信息成功')
            account_info = regex_csgo_account_info(account_re)
            self.update_table_item_request.emit(self.row_index, 6, f"{account_info['rank']}")
            self.update_table_item_request.emit(self.row_index, 7, f"{account_info['exp']}")
            return True, account_info
        self.update_table_item_request.emit(self.row_index, 1, '获取CSGO账户信息失败')
        return False, None

    def vac_check_task(self):
        self.update_table_item_request.emit(self.row_index, 1, '正在获取VAC状态...')
        state, vac_re = self.acc.get_vac_status()
        if state:
            self.update_table_item_request.emit(self.row_index, 1, '获取VAC状态成功')
            vac, vac_mes = regex_vac_status(vac_re)
            self.update_table_item_request.emit(self.row_index, 4, f"{vac},{vac_mes}")
            return True, vac
        self.update_table_item_request.emit(self.row_index, 1, '获取VAC状态失败')
        return False, None

    def inventory_task(self):
        self.update_table_item_request.emit(self.row_index, 1, '正在获取掉落信息...')
        inventory_state, inventory_re = self.acc.get_history_inventory()
        if inventory_state:
            self.update_table_item_request.emit(self.row_index, 1, '获取掉落信息成功')
            inventory_list = regex_recently_dropped(inventory_re)
            if inventory_list:
                if inventory_list[0]['date'] == inventory_list[1]['date']:
                    # 将 裂空武器箱,P250 | 沙丘之黄 分成两个
                    self.check_rare_drop(inventory_list[1]['item_name'])
                    self.update_table_item_request.emit(self.row_index, 2,
                                                        f"{inventory_list[1]['item_name']}, {inventory_list[0]['item_name']}")
                    self.update_table_item_request.emit(self.row_index, 3,
                                                        f"{inventory_list[0]['date']}")
                else:
                    self.update_table_item_request.emit(self.row_index, 2,
                                                        f"{inventory_list[0]['item_name']}")
                    self.update_table_item_request.emit(self.row_index, 3,
                                                        f"{inventory_list[0]['date']}")
                # 如果 inventory_list[0]['date'] 小于本周三上午10点，那么就是上周的掉落

                self.update_table_item_request.emit(self.row_index, 5,
                                                    f"{is_this_week_drop(inventory_list[0]['date'])}")
                return True, inventory_list
            else:
                self.update_table_item_request.emit(self.row_index, 2, '未掉落')
                return False, None
        self.update_table_item_request.emit(self.row_index, 1, '获取掉落信息失败')
        return False, None


class Ui_LoginWindow(QMainWindow, Ui_login_MainWindow):
    def __init__(self):
        super(Ui_LoginWindow, self).__init__()
        self.setupUi(self)  # 使用 Ui_login_MainWindow 来设置界面

    def handle_login(self):
        username = self.lineEdit_2.text()
        password = self.lineEdit.text()
        if self.validate_credentials(username, password) or True:
            self.main_window = Ui_MainWindow()
            self.main_window.show()
            self.close()
        else:
            QtWidgets.QMessageBox.warning(self, '错误', '用户名或密码错误')

    def validate_credentials(self, username, password):
        # 简单的验证逻辑
        return username == "admin" and password == "password"


class Ui_MainWindow(QMainWindow, Ui_task_MainWindow):
    def __init__(self):
        # 初始化代码...
        self.taskQueue = Queue()  # 创建一个任务队列
        self.activeThreads = 0  # 当前活跃的线程数
        self.maxThreads = 1  # 最大并发线程数
        self.threadList = []  # 用于存储所有线程的列表
        self.workerList = []
        self.isRunning = False  # 追踪任务是否正在运行
        super(Ui_MainWindow, self).__init__()
        self.setupUi(self)  # 使用 Ui_MainWindow 来设置界面
        self.load_accounts_from_db()

    def update_table_item(self, row_index, col_index, text):
        item = self.accTable.item(row_index, col_index)
        if item:
            item.setText(text)
        else:
            self.accTable.setItem(row_index, col_index, QtWidgets.QTableWidgetItem(text))

    def get_table_item(self, row_index, col_index):
        item = self.accTable.item(row_index, col_index)
        if item:
            return item.text()
        else:
            return None

    def log_message(self, message):
        self.msgEdit.append(message)

    def load_accounts_from_file(self):
        filePath, _ = QFileDialog.getOpenFileName(None, "选择账号文件", "", "Text Files (*.txt)")
        if filePath:
            with open(filePath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                # 目前Table的所有行数
                row_counts = self.accTable.rowCount()
                sql_handler = SQLHandler()
                # 获取目前数据库的所有账号，计算增量部分
                db_accounts = sql_handler.get_all_accounts()
                # db_accounts 获取 user_account 存入 list
                if db_accounts:
                    db_accounts_user_name = [account[0] for account in db_accounts]
                else:
                    db_accounts_user_name = []
                file_accounts = []
                for line in lines:
                    account_info = line.strip().split(':')
                    account = account_info[0]
                    password = account_info[1]
                    if account not in db_accounts_user_name:
                        file_accounts.append({'account': account, 'password': password})
                # 录入数据库
                if file_accounts:
                    for account_info in file_accounts:
                        sql_handler.insert_or_update(account_info['account'], account_info['password'], '', '', '',
                                                     0, '', '', '')
                sql_handler.conn.close()
                # 重新加载数据库
                self.load_accounts_from_db()

    def load_accounts_from_db(self):
        global g_accounts
        sql_handler = SQLHandler()
        accounts = sql_handler.get_all_accounts()
        # 如果 accounts 不为 None
        if accounts and len(accounts) > 0:
            g_accounts = accounts
        self.accTable.setRowCount(len(g_accounts))
        for rowIndex, account in enumerate(g_accounts):
            for columnIndex, item in enumerate(account):
                if columnIndex < self.accTable.columnCount() and columnIndex < 1:
                    self.accTable.setItem(rowIndex, columnIndex, QtWidgets.QTableWidgetItem(item))
        sql_handler.conn.close()

    def toggle_task(self):
        if not self.isRunning:
            self.start_task()
        else:
            self.stop_task()

    def start_task(self):
        # 清空日志
        self.msgEdit.clear()
        thread_num = int(self.threadNumEdit.text())  # 获取文本内容
        if thread_num:
            self.maxThreads = thread_num
        else:
            self.maxThreads = 1
        if self.accTable.rowCount() > 0:
            # 更新运行状态
            self.isRunning = 1
            self.startTaskBut.setText("停止")
            self.startTaskBut.setEnabled(True)
            self.threadList.clear()
            rowCount = self.accTable.rowCount()
            for rowIndex in range(rowCount):
                account = self.accTable.item(rowIndex, 0).text()
                # 将任务参数作为元组加入队列
                self.taskQueue.put((account, rowIndex))

            # 尝试启动初始的一组线程
            for _ in range(min(self.maxThreads, self.taskQueue.qsize())):
                self.start_next_task()

    def stop_task(self):
        if len(self.workerList) == 0 and len(self.threadList) == 0:
            self.isRunning = 0
            self.startTaskBut.setText("开始")
            self.startTaskBut.setEnabled(False)  # 设置按钮为不可点击
        else:
            self.isRunning = 2
            self.startTaskBut.setText("停止中")
            self.startTaskBut.setEnabled(False)  # 设置按钮为不可点击

    def start_next_task(self):
        if not self.taskQueue.empty() and self.activeThreads < self.maxThreads and self.isRunning == 1:
            account, rowIndex = self.taskQueue.get()
            thread = QThread()
            worker = Worker(account, rowIndex)
            worker.moveToThread(thread)
            worker.update_table_item_request.connect(self.update_table_item)
            worker.get_table_item.connect(self.get_table_item)
            worker.log_message.connect(self.log_message)
            worker.finished.connect(lambda: self.on_task_finished(thread, worker))
            thread.started.connect(worker.run)

            thread.start()
            self.activeThreads += 1
            self.workerList.append(worker)
            self.threadList.append(thread)  # 将线程添加到列表中
        elif self.isRunning == 2 and len(self.workerList) == 0 and len(self.threadList) == 0:
            self.isRunning = 0
            self.startTaskBut.setText("开始")
            self.startTaskBut.setEnabled(True)

    def on_task_finished(self, thread, worker):
        # 线程完成时的清理工作
        thread.quit()
        thread.wait()
        thread.deleteLater()
        self.activeThreads -= 1
        try:
            self.workerList.remove(worker)
        except ValueError:
            pass  # 这里忽略错误，因为worker可能已经被移除
        self.threadList.remove(thread)  # 从列表中移除已完成的线程

        # 检查是否所有任务都已完成
        if self.taskQueue.empty() and self.activeThreads == 0:
            # 所有任务完成后的操作
            QMessageBox.information(None, "任务完成", "所有任务已经完成！")
            self.startTaskBut.setText("开始")
            self.startTaskBut.setEnabled(True)  # 重新启用开始按钮
            self.isRunning = 0  # 更新运行状态标记为不运行

        # 尝试启动下一个等待中的任务
        self.start_next_task()

    def openMenu(self, position):
        menu = QMenu()

        # 添加全选动作
        selectAllAction = menu.addAction("导出所有账号")
        selectAllAction.triggered.connect(self.export_all)

        # 选中掉落数量大于0的账户
        invertSelectionAction = menu.addAction("导出本周稀有掉落账户")
        invertSelectionAction.triggered.connect(self.export_this_week_rare_accounts)

        # 选中本周掉落等于0的账户
        invertSelectionAction = menu.addAction("导出本周未掉落的账户")
        invertSelectionAction.triggered.connect(self.export_week_drop_eq_0)

        # 导出vac账户
        deleteSelectedAction = menu.addAction("导出vac账户")
        deleteSelectedAction.triggered.connect(self.export_vac_accounts)

        # 显示菜单
        menu.exec_(self.accTable.viewport().mapToGlobal(position))

    def export_all(self):
        # 查询数据库
        sql_handler = SQLHandler()
        accounts = sql_handler.get_all_accounts()
        sql_handler.conn.close()
        self.export(['账号', '密码'], accounts)

    def export_this_week_rare_accounts(self):
        # 查询数据库
        sql_handler = SQLHandler()
        accounts = sql_handler.get_rare_drop_accounts()
        sql_handler.conn.close()
        self.export(['账号', '密码', '稀有掉落'], accounts)

    def export_week_drop_eq_0(self):
        # 查询数据库
        sql_handler = SQLHandler()
        accounts = sql_handler.get_week_drop_eq_0()
        sql_handler.conn.close()
        self.export(['账号', '密码', '等级', '经验'], accounts)

    def export_vac_accounts(self):
        # 查询数据库
        sql_handler = SQLHandler()
        accounts = sql_handler.get_vac_accounts()
        sql_handler.conn.close()
        self.export(['账号', '密码', 'VAC状态'], accounts)

    def export(self, titles, data=[]):
        # 创建一个工作簿
        workbook = Workbook()
        sheet = workbook.active
        column_titles = titles
        sheet.append(column_titles)  # 将列标题添加到第一行
        # 遍历表格的每一行
        for item in data:
            sheet.append(item)
        # 弹出文件保存对话框，让用户选择保存位置和文件名
        fileName, _ = QFileDialog.getSaveFileName(None, "保存文件", "", "Excel文件 (*.xlsx)")

        if fileName:
            # 保存工作簿到指定的文件
            workbook.save(fileName)
            # 提示保存成功
            QMessageBox.information(None, "导出成功", f"已成功导出到 {fileName},共 {len(data)} 条记录")


import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = Ui_LoginWindow()
    login_window.show()
    sys.exit(app.exec_())
