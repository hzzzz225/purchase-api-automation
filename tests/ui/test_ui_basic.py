from pathlib import Path

import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

pytestmark = pytest.mark.ui

@pytest.fixture
def driver():
    """
    初始化 Chrome 浏览器。
    每个测试用例执行后自动关闭浏览器。
    """
    options = webdriver.ChromeOptions()

    browser = webdriver.Chrome(options=options)
    browser.maximize_window()

    yield browser

    browser.quit()


@pytest.fixture
def open_demo_page(driver):
    """
    打开本地 Selenium 练习页面。
    """
    page_path = Path(__file__).resolve().parents[2] / "ui_demo.html"

    driver.get(page_path.as_uri())

    return driver


def test_page_title(open_demo_page):
    """
    测试页面标题是否正确。
    """
    title = open_demo_page.find_element(
        By.ID, "page-title"
    ).text

    assert title == "采购管理系统登录"


def test_login_success(open_demo_page):
    """
    测试正确用户名和密码能否登录。
    """
    driver = open_demo_page

    driver.find_element(By.ID, "username").send_keys("tester")
    driver.find_element(By.NAME, "password").send_keys("123456")

    driver.find_element(By.CSS_SELECTOR, ".primary-btn").click()

    result = driver.find_element(By.ID, "login-result").text

    assert result == "登录成功"


def test_login_failed(open_demo_page):
    """
    测试错误密码能否得到预期提示。
    """
    driver = open_demo_page

    driver.find_element(By.ID, "username").send_keys("tester")
    driver.find_element(By.ID, "password").send_keys("wrong")

    driver.find_element(By.ID, "login-btn").click()

    result = driver.find_element(By.ID, "login-result").text

    assert result == "用户名或密码错误"


def test_create_order_success(open_demo_page):
    """
    测试创建订单，并使用显式等待。
    """
    driver = open_demo_page

    driver.find_element(
        By.ID, "product-name"
    ).send_keys("测试商品")

    driver.find_element(
        By.ID, "quantity"
    ).send_keys("10")

    driver.find_element(
        By.XPATH, "//button[@id='create-btn']"
    ).click()

    result_element = WebDriverWait(driver, 5).until(
        EC.text_to_be_present_in_element(
            (By.ID, "order-result"),
            "订单创建成功"
        )
    )

    result = driver.find_element(
        By.ID, "order-result"
    ).text

    assert "测试商品" in result
    assert "数量：10" in result
