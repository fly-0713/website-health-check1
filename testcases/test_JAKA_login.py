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
    """JAKA 官网登录测试用例"""

    @pytest.mark.parametrize(
        "data",
        jaka_login_data,
        ids=[d["case_name"] for d in jaka_login_data],
    )
    def test_jaka_login(self, page: Page, data: dict):
        """JAKA 官网密码登录，断言页面出现"退出登录" """
        logger.info(f"开始测试: {data['case_name']}")

        jaka_account = config.get_jaka_account()
        username = jaka_account.get("username") or data.get("username")
        password = jaka_account.get("password") or data.get("password")
        
        logger.info(f"JAKA 官网登录用户名: {username}")

        login_page = JakaLoginPage(page)
        
        # 重试机制
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            logger.info(f"登录尝试 {attempt}/{max_retries}")
            
            try:
                login_page.navigate(config.jaka_base_url)
                success, api_response_time = login_page.login_until_success(
                    username=username,
                    password=password,
                )
                
                if success:
                    logger.info(f"✅ 测试通过: {data['case_name']}")
                    logger.info(f"📊 API 响应时间: {api_response_time:.3f}秒")
                    return
                else:
                    logger.warning(f"第 {attempt} 次登录失败，准备重试...")
                    page.reload()
                    page.wait_for_timeout(2000)
                    
            except Exception as e:
                logger.error(f"第 {attempt} 次尝试异常: {e}")
                if attempt == max_retries:
                    raise
                page.wait_for_timeout(3000)
        
        assert False, f"JAKA 官网登录失败：连续 {max_retries} 次尝试均未成功"