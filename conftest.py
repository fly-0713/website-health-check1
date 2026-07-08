import os
import sys

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import allure
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from common.logger import logger, get_case_log, clear_case_log
from common.screenshot import take_screenshot


# 测试文件执行顺序（按此列表顺序运行，未在列表中的文件按字母顺序追加到末尾）
TEST_FILE_ORDER = [
    "test_login.py",
    "test_JAKA_login.py",
]


def pytest_collection_modifyitems(items):
    """按照 TEST_FILE_ORDER 排序测试用例收集顺序"""
    def sort_key(item):
        filename = os.path.basename(item.fspath)
        try:
            return TEST_FILE_ORDER.index(filename)
        except ValueError:
            # 未在列表中的文件，排到最后
            return len(TEST_FILE_ORDER)

    items.sort(key=sort_key)


def pytest_addoption(parser):
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="无头模式运行浏览器",
    )


# shared_data 已改用文件存储方式（common/shared_data.py），
# 数据持久化到 datas/shared_data.json，解耦测试依赖
# 使用方式：from common.shared_data import shared_data


@pytest.fixture(scope="session")
def browser(pytestconfig):
    """\u542f\u52a8\u6d4f\u89c8\u5668\uff0csession \u7ea7\u522b\u5171\u4eab"""
    # config \u5728\u6b64\u5904\u5bfc\u5165\uff0c\u786e\u4fdd ENV \u5df2\u7531 main.py \u8bbe\u7f6e\u540e\u518d\u52a0\u8f7d
    from common.config import config  # noqa
    # \u9ed8\u8ba4\u6709\u5934\u6a21\u5f0f\uff0c\u53ea\u6709\u663e\u5f0f\u4f20 --headless \u624d\u65e0\u5934
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
