import sqlite3

# 个人信息表
user_info_table = '''
CREATE TABLE IF NOT EXISTS user_info(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_account TEXT NOT NULL UNIQUE,
    user_password TEXT,
    drop_time TEXT,
    drop_item TEXT,
    drop_num INTEGERL,
    vac_status INTEGERL,
    is_this_week_drop INTEGER,
    rank INTEGER,
    exp INTEGER,
    session TEXT
    );
'''

# 定义普通箱子的名称数组
normal_boxes = [
    "梦魇武器箱",
    "千瓦武器箱",
    "反冲武器箱",
    "变革武器箱",
    "裂空武器箱",
]

class SQLHandler:
    def __init__(self, db_name='user_info.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

        # 如果表不存在则创建表
        self.cursor.execute(user_info_table)
        self.conn.commit()

    # 获取个人信息的掉落时间,根据掉落时间判断是否是本周掉落
    def get_drop_time(self, user_account):
        self.cursor.execute(
            'SELECT drop_time FROM user_info WHERE user_account = ?',
            (user_account,)
        )
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def get_user_info(self, user_account):
        self.cursor.execute(
            'SELECT * FROM user_info WHERE user_account = ?',
            (user_account,)
        )
        result = self.cursor.fetchone()
        if result:
            return result
        return None

    def insert_or_update(self, user_account, user_password, drop_time, drop_item, drop_num, vac_status,
                         is_this_week_drop, rank,
                         exp):
        # 判断是否存在
        if self.get_user_info(user_account):
            self.cursor.execute(
                'UPDATE user_info SET user_password = ?, drop_time = ?, drop_item = ?, drop_num = ?, vac_status = ?, is_this_week_drop = ?, rank = ?, exp = ? WHERE user_account = ?',
                (user_password, drop_time, drop_item, drop_num, vac_status, is_this_week_drop, rank, exp, user_account)
            )

        else:
            self.cursor.execute(
                'INSERT INTO user_info(user_account, user_password, drop_time, drop_item, drop_num, vac_status, is_this_week_drop, rank, exp) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (user_account, user_password, drop_time, drop_item, drop_num, vac_status, is_this_week_drop, rank, exp)
            )
        self.conn.commit()

    def get_all_accounts(self):
        self.cursor.execute('SELECT user_account,user_password FROM user_info')
        result = self.cursor.fetchall()
        if result:
            return result
        return None

    def set_account_session(self, user_account, session):
        if self.get_user_info(user_account):
            self.cursor.execute(
                'UPDATE user_info SET session = ? WHERE user_account = ?',
                (session, user_account)
            )
        else:
            self.cursor.execute(
                'INSERT INTO user_info(user_account, session) VALUES(?, ?)',
                (user_account, session)
            )
        self.conn.commit()

    def get_account_session(self, user_account):
        self.cursor.execute(
            'SELECT session FROM user_info WHERE user_account = ?',
            (user_account,)
        )
        result = self.cursor.fetchone()
        if result:
            return result[0]
        return None

    def get_rare_drop_accounts(self):
        self.cursor.execute('SELECT user_account,user_password,drop_item FROM user_info WHERE is_this_week_drop = 1')
        result = self.cursor.fetchall()
        # foreach 每一条数据
        rare_drop_accounts = []
        for data in result:
            if data[2].split(',')[0] not in normal_boxes:
                rare_drop_accounts.append(data)
        return rare_drop_accounts

    def get_week_drop_eq_0(self):
        self.cursor.execute('SELECT user_account,user_password,rank,exp FROM user_info WHERE is_this_week_drop = 0')
        result = self.cursor.fetchall()
        return result

    def get_vac_accounts(self):
        self.cursor.execute('SELECT user_account,user_password FROM user_info WHERE vac_status = 1')
        result = self.cursor.fetchall()
        return result

