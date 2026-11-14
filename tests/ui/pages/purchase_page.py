
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC


class LoginPage:
    """登录页面对象"""

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def login(self, username, password):

        self.driver.find_element(
            By.ID, "username"
        ).clear()

        self.driver.find_element(
            By.ID, "username"
        ).send_keys(username)

        self.driver.find_element(
            By.ID, "password"
        ).clear()

        self.driver.find_element(
            By.ID, "password"
        ).send_keys(password)

        self.driver.find_element(
            By.ID, "login-btn"
        ).click()

        self.wait.until(
            EC.visibility_of_element_located(
                (By.ID, "purchase-panel")
            )
        )

        self.wait.until(
            lambda d: len(
                Select(
                    d.find_element(By.ID, "supplier-id")
                ).options
            ) > 0
        )

        return self.driver.find_element(
            By.ID, "login-result"
        ).text


class PurchasePage:
    """采购订单页面对象"""

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    def create_order(
        self,
        supplier_id,
        product_id,
        quantity,
        remark
    ):
        # 选择供应商
        Select(
            self.driver.find_element(By.ID, "supplier-id")
        ).select_by_value(str(supplier_id))

        # 选择商品
        Select(
            self.driver.find_element(By.ID, "product-id")
        ).select_by_value(str(product_id))

        # 等待商品单价加载
        self.wait.until(
            lambda d: d.find_element(
                By.ID, "unit-price"
            ).get_attribute("value") != ""
        )

        # 输入采购数量
        quantity_input = self.driver.find_element(
            By.ID, "quantity"
        )

        quantity_input.clear()
        quantity_input.send_keys(str(quantity))

        # 输入唯一备注
        remark_input = self.driver.find_element(
            By.ID, "remark"
        )

        remark_input.clear()
        remark_input.send_keys(remark)

        # 创建订单
        self.driver.find_element(
            By.ID, "create-btn"
        ).click()

        # 等待订单编号出现
        self.wait.until(
            lambda d: d.find_element(
                By.ID, "order-id"
            ).text.strip() not in ("", "暂无")
        )

        # 等待初始状态
        self.wait.until(
            lambda d: d.find_element(
                By.ID, "order-status"
            ).text.strip() == "PENDING"
        )

        order_id = self.driver.find_element(
            By.ID, "order-id"
        ).text

        return int(order_id)

    def get_stock_info(self):
        return self.driver.find_element(
            By.ID, "stock-info"
        ).text

    def get_order_status(self):
        return self.driver.find_element(
            By.ID, "order-status"
        ).text.strip()

    def approve_order(self):

        self.driver.find_element(
            By.ID, "approve-btn"
        ).click()

        self.wait.until(
            lambda d: d.find_element(
                By.ID, "order-status"
            ).text.strip() == "APPROVED"
        )

        return self.get_order_status()

    def receive_order(self):

        self.driver.find_element(
            By.ID, "receive-btn"
        ).click()

        self.wait.until(
            lambda d: d.find_element(
                By.ID, "order-status"
            ).text.strip() == "RECEIVED"
        )

        return self.get_order_status()
