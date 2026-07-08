"""JAKA 官网登录页面对象

JAKA 官网（Nuxt.js）登录流程：
  1. 打开首页，点击"登录"入口
  2. 切换到"密码登录"标签
  3. 填写手机号/邮箱 + 密码
  4. 勾选用户协议复选框
  5. 点击登录按钮
  6. 登录成功判断：页面出现"退出登录"
"""

import time
from playwright.sync_api import Page

from common.logger import logger
from pages.base_page import BasePage


class JakaLoginPage(BasePage):
    """JAKA 官网登录页面对象"""

    def __init__(self, page: Page):
        super().__init__(page)
        # 首页"登录"入口 - 使用更精确的定位
        self._login_entry = page.locator("a:has-text('登录')").first
        # "密码登录"标签 - 用 CSS 类选择器精确定位
        self._password_login_tab = page.locator(".tab .item.f_16", has_text="密码登录")
        # 手机/邮箱输入框
        self._username_input = page.get_by_placeholder("请输入您的注册手机或者邮箱")
        # 密码输入框（仅在"密码登录"标签激活后才出现）
        self._password_input = page.get_by_placeholder("请输入您的密码")
        # 用户协议复选框 - 限定在登录弹窗范围内
        self._agree_checkbox = page.locator(".login #comm")
        # 登录按钮 - 使用 class 精确定位
        self._login_button = page.locator(".login .submit")
        # 登录成功标志：退出登录
        self._logout_text = page.get_by_text("退出登录")
        # 登录弹窗容器
        self._login_dialog = page.locator(".login .inner")
        
        # 🔥 存储 API 响应时间
        self._api_response_time = 0

    def navigate(self, url: str):
        """打开 JAKA 官网首页并等待登录入口加载"""
        # JAKA 官网资源较多，CI 中容易超时，使用 domcontentloaded + 60s 超时
        super().navigate(url, wait_until="domcontentloaded", timeout=60000)
        # 等待登录入口可见
        self.wait_for_visible(self._login_entry)
        logger.info(f"JAKA 官网首页加载完成，URL: {self.page.url}")

    def login(self, username: str, password: str):
        """执行完整登录流程：打开弹窗 → 切换密码登录 → 填写 → 勾选协议 → 点击登录"""
        # 点击首页"登录"入口，打开登录弹窗
        logger.info("点击首页登录入口")
        
        # 确保登录按钮可见并可点击
        self._login_entry.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)
        
        # 使用 JavaScript 点击，绕过可能的遮挡
        self._login_entry.evaluate("element => element.click()")
        
        # 等待登录弹窗出现（增加超时时间）
        logger.info("等待登录弹窗出现...")
        try:
            self._login_dialog.wait_for(state="visible", timeout=15000)
            logger.info("登录弹窗已出现")
        except Exception as e:
            logger.error(f"登录弹窗未出现: {e}")
            self.page.screenshot(path="login_dialog_not_found.png")
            raise
        
        # 额外等待动画完成
        self.page.wait_for_timeout(1000)
        
        # 切换到密码登录标签
        self._switch_to_password_login()
        
        # 填写手机号/邮箱
        logger.info(f"填写手机号/邮箱: {username}")
        self.click_and_fill(self._username_input, username)
        
        # 填写密码
        logger.info("填写密码")
        self.click_and_fill(self._password_input, password)
        
        # 勾选用户协议
        logger.info("勾选用户协议复选框")
        try:
            self._agree_checkbox.check(timeout=self.timeout)
        except Exception as e:
            logger.warning(f"勾选协议失败，尝试点击: {e}")
            self._agree_checkbox.click()
        
        # 🔥 点击登录并测量 API 响应时间
        logger.info("点击登录按钮，测量响应时间...")
        self._measure_login_response_time()

    def _measure_login_response_time(self):
        """测量登录 API 响应时间"""
        try:
            # 监听登录 API 请求
            with self.page.expect_response(
                lambda response: "login" in response.url.lower() or "auth" in response.url.lower(),
                timeout=15000
            ) as response_info:
                self.click(self._login_button)
            
            response = response_info.value
            timing = response.timing
            if timing:
                self._api_response_time = (timing.get("responseEnd", 0) - timing.get("requestStart", 0)) / 1000
                logger.info(f"登录 API 响应时间: {self._api_response_time:.3f}秒")
                logger.info(f"登录 API 状态码: {response.status}")
            else:
                self._api_response_time = 0
                logger.warning("无法获取 API 响应时间")
                
        except Exception as e:
            logger.warning(f"测量 API 响应时间失败: {e}")
            self._api_response_time = 0

    def _switch_to_password_login(self, max_retries: int = 3):
        """切换到密码登录标签，通过检测密码输入框是否出现来确认切换成功"""
        for attempt in range(1, max_retries + 1):
            logger.info(f"切换到密码登录 (尝试 {attempt}/{max_retries})")
            
            # 使用 JavaScript 点击标签
            self._password_login_tab.evaluate("element => element.click()")
            self.page.wait_for_timeout(500)
            
            try:
                self._password_input.wait_for(state="visible", timeout=5000)
                logger.info("密码登录标签已切换")
                return
            except Exception:
                if attempt < max_retries:
                    logger.warning("密码登录标签未切换，等待后重试...")
                    self.page.wait_for_timeout(1000)
                else:
                    raise TimeoutError(
                        f"连续 {max_retries} 次点击密码登录标签均未切换成功"
                    )

    def login_until_success(self, username: str, password: str) -> tuple:
        """执行登录并等待成功，返回 (是否成功, API响应时间)"""
        try:
            # 记录整体开始时间
            total_start = time.time()
            
            self.login(username, password)
            success = self._wait_for_login_result()
            
            # 计算整体耗时
            total_time = time.time() - total_start
            
            # 如果没有测量到 API 响应时间，使用整体耗时
            if self._api_response_time == 0:
                self._api_response_time = total_time
                logger.info(f"使用整体耗时作为响应时间: {self._api_response_time:.3f}秒")
            
            logger.info(f"测试总耗时: {total_time:.3f}秒, API响应: {self._api_response_time:.3f}秒")
            
            return success, self._api_response_time
            
        except Exception as e:
            logger.error(f"登录过程异常: {e}")
            self.page.screenshot(path="login_error.png")
            return False, 0

    def _wait_for_login_result(self, timeout: int = 15000) -> bool:
        """等待登录结果：页面出现"退出登录"即成功，超时即失败"""
        try:
            self._logout_text.wait_for(state="visible", timeout=timeout)
            logger.info("登录成功，已检测到'退出登录'")
            return True
        except Exception as e:
            logger.error(f"等待'退出登录'超时，登录失败: {e}")
            return False