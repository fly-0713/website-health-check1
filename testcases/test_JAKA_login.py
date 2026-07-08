import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from playwright.sync_api import Page

from common.config import config
from common.logger import logger
from datas.jaka_login_data import jaka_login_data
from pages.jaka_login_page import JakaLoginPage


class TestJakaLogin:
    """JAKA 官网登录测试用例

    JAKA 官网使用独立的 URL 和账号，不依赖 MES 配置，
    可与其他用例在同一次 pytest 运行中共存。
    """

    @pytest.mark.parametrize(
        "data",
        jaka_login_data,
        ids=[d["case_name"] for d in jaka_login_data],
    )
    def test_jaka_login(self, page: Page, data: dict):
        """JAKA 官网密码登录，断言页面出现"退出登录" """
        logger.info(f"开始测试: {data['case_name']}")

        # 从配置中获取 JAKA 官网账号
        jaka_account = config.get_jaka_account()
        username = jaka_account.get("username") or data.get("username")
        password = jaka_account.get("password") or data.get("password")
        
        logger.info(f"JAKA 官网登录用户名: {username}")

        login_page = JakaLoginPage(page)
        login_page.navigate(config.jaka_base_url)

        success = login_page.login_until_success(
            username=username,
            password=password,
        )

        assert success, "JAKA 官网登录失败：未检测到'退出登录'，请检查账号或网络"
        logger.info(f"✅ 测试通过: {data['case_name']}，已成功登录 JAKA 官网")