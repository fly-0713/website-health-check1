import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from playwright.sync_api import Page

from common.config import config
from common.logger import logger
from datas.login_data import login_data
from pages.login_page import LoginPage


class TestLogin:
    """MES 后台登录测试用例"""

    @pytest.mark.parametrize(
        "data",
        login_data,
        ids=[d["case_name"] for d in login_data],
    )
    def test_login(self, page: Page, data: dict):
        """自动识别验证码登录，失败则重试直到成功"""
        logger.info(f"开始测试: {data['case_name']}")
        
        # 从配置中获取 MES 账号（支持环境变量替换）
        account = config.get_account()
        username = account.get("username") or data.get("username")
        password = account.get("password") or data.get("password")
        
        logger.info(f"MES 后台登录用户名: {username}")
        
        login_page = LoginPage(page)
        login_page.navigate(config.base_url)

        success = login_page.login_until_success(
            username=username,
            password=password,
        )

        assert success, f"MES 后台登录失败：连续 {LoginPage.MAX_RETRY} 次验证码识别错误"
        logger.info(f"测试通过: {data['case_name']}，已成功进入首页")