import os
import sys

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import allure
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from common.config import config
from common.logger import logger, get_case_log, clear_case_log
from common.screenshot import take_screenshot


def pytest_addoption(parser):
    """注册自定义命令行参数"""
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="无头模式运行浏览器",
    )


@pytest.fixture(scope="session")
def browser(pytestconfig):
    """启动浏览器，session 级别共享"""
    # 默认有头模式，只有显式传 --headless 才无头
    headless = pytestconfig.getoption("--headless")
    pw = sync_playwright().start()
    browser = pw.chromium.launch(headless=headless)
    mode = "无头模式" if headless else "有头模式"
    logger.info(f"浏览器已启动（{mode}）")
    yield browser
    browser.close()
    pw.stop()
    logger.info("浏览器已关闭")


@pytest.fixture(scope="function")
def context(browser: Browser):
    """每个测试用例创建独立的上下文"""
    context = browser.new_context()
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext):
    """每个测试用例创建独立的页面"""
    page = context.new_page()
    yield page


@pytest.fixture(autouse=True)
def _setup_case_log():
    """每个用例开始前清空日志缓冲，结束后附加到 allure"""
    clear_case_log()
    yield
    # 用例结束后将缓冲日志附加到 allure
    case_log = get_case_log()
    if case_log:
        allure.attach(case_log, name="用例日志", attachment_type=allure.attachment_type.TEXT)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """断言失败时自动截图并附加到 allure"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            case_name = item.nodeid.replace("::", "_").replace("/", "_")
            logger.error(f"测试失败，自动截图: {case_name}")
            filepath = take_screenshot(page, case_name)
            with open(filepath, "rb") as f:
                allure.attach(
                    f.read(),
                    name=f"{case_name}_失败截图",
                    attachment_type=allure.attachment_type.PNG,
                )
