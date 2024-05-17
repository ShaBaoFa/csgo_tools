import sqlite3

# 个人信息表
user_info_table = '''
CREATE TABLE IF NOT EXISTS user_info(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_account TEXT NOT NULL UNIQUE,
    user_password TEXT NOT NULL,
    drop_time TEXT NOT NULL,
    drop_item TEXT NOT NULL,
    drop_num INTEGER NOT NULL,
    vac_status INTEGER NOT NULL,
    is_this_week_drop INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    exp INTEGER NOT NULL
);
'''


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
        print('user_account:', user_account)
        if self.get_user_info(user_account):
            print('update')
            self.cursor.execute(
                'UPDATE user_info SET user_password = ?, drop_time = ?, drop_item = ?, drop_num = ?, vac_status = ?, is_this_week_drop = ?, rank = ?, exp = ? WHERE user_account = ?',
                (user_password, drop_time, drop_item, drop_num, vac_status, is_this_week_drop, rank, exp, user_account)
            )

        else:
            print('insert')
            self.cursor.execute(
                'INSERT INTO user_info(user_account, user_password, drop_time, drop_item, drop_num, vac_status, is_this_week_drop, rank, exp) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (user_account, user_password, drop_time, drop_item, drop_num, vac_status, is_this_week_drop, rank, exp)
            )
        self.conn.commit()
