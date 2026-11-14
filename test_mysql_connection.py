
import pymysql

from config.db_config import DB_CONFIG


def test_mysql_connection():
    connection = None

    try:
        # 建立数据库连接
        connection = pymysql.connect(
            **DB_CONFIG
        )

        print("MySQL 连接成功")

        # 创建游标
        cursor = connection.cursor()

        # 执行 SQL
        cursor.execute("SELECT VERSION()")

        # 获取查询结果
        result = cursor.fetchone()

        print("MySQL 版本：", result[0])

        cursor.close()

    except pymysql.MySQLError as e:
        print("MySQL 操作失败：", e)
        raise

    finally:
        if connection:
            connection.close()
            print("数据库连接已关闭")


if __name__ == "__main__":
    test_mysql_connection()
