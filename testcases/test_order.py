import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from playwright.sync_api import Page

from common.config import config
from common.logger import logger
from pages.login_page import LoginPage
from pages.order_page import OrderPage


class TestOrder:
    """计划订单测试用例"""

    def test_order(self, page: Page):
        """登录后搜索计划编号，验证查询结果包含关键字"""
        logger.info("开始测试: 计划订单搜索")

        # 1. 登录
        login_page = LoginPage(page)
        login_page.navigate(config.base_url)
        success = login_page.login_until_success(
            username=config.get_account(0)["username"],
            password=config.get_account(0)["password"],
        )
        assert success, "登录失败"

        # 2. 导航到计划订单页面
        order_page = OrderPage(page)
        order_page.navigate_to_order()

        # 3. 输入计划编号并搜索
        search_keyword = "test"
        order_page.search_order(search_keyword)

        # 4. 断言搜索结果不为空，且每条计划编号包含 test 或 TEST
        order_numbers = order_page.get_order_numbers()
        assert len(order_numbers) > 0, f"搜索 '{search_keyword}' 结果为空"
        for no in order_numbers:
            assert "test" in no.lower(), f"计划编号 '{no}' 不包含 '{search_keyword}'"
        logger.info(f"测试通过: 搜索 '{search_keyword}' 返回 {len(order_numbers)} 条，均包含关键字")
