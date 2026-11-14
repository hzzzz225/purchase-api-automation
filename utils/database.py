
import pymysql

from config.db_config import DB_CONFIG


class Database:

    def __init__(self):
        # 建立数据库连接
        self.connection = pymysql.connect(
            **DB_CONFIG
        )

    def fetch_one(self, sql, params=None):
        """查询一条记录"""
        with self.connection.cursor(
            pymysql.cursors.DictCursor
        ) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def fetch_all(self, sql, params=None):
        """查询所有记录"""
        with self.connection.cursor(
            pymysql.cursors.DictCursor
        ) as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()

    def execute(self, sql, params=None):
        """执行 INSERT、UPDATE、DELETE 等写操作"""
        with self.connection.cursor() as cursor:
            affected_rows = cursor.execute(sql, params)

        self.connection.commit()

        return affected_rows

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
