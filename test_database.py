
from utils.database import Database


def test_database_query():
    db = Database()

    try:
        # 查询一条商品记录
        result = db.fetch_one(
            "SELECT * FROM test_product WHERE id = %s",
            (1,)
        )

        print("查询结果：", result)

        assert result is not None
        assert result["product_name"] == "测试商品A"
        assert result["stock"] == 100

        # 查询所有商品
        results = db.fetch_all(
            "SELECT * FROM test_product"
        )

        print("商品数量：", len(results))

        assert len(results) >= 2

    finally:
        db.close()
