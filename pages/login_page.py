import time

from playwright.sync_api import Page, Locator

from common.captcha_ocr import recognize_from_bytes
from common.config import config
from common.logger import logger
from pages.base_page import BasePage

# 登录失败时的提示关键字
CAPTCHA_ERROR_KEYWORD = "输入验证码有误"


class LoginPage(BasePage):
    """登录页面对象"""

    MAX_RETRY = 10

    # 登录页 URL 关键路径（用于判断是否仍在登录页）
    LOGIN_URL_KEYWORD = "/#/login?backUrl=/"

    # 登录失败提示关键字（支持多种提示文本）
    ERROR_KEYWORDS = ["验证码", "有误", "错误", "不正确", "失败"]

    def __init__(self, page: Page):
        super().__init__(page)
        # 元素定位器
        self._username_input = page.get_by_placeholder("用户名")
        self._password_input = page.get_by_placeholder("密码")
        self._captcha_input = page.get_by_placeholder("验证码")
        self._login_button = page.get_by_role("button", name="登录")
        self._message_paragraph = page.get_by_role("paragraph")
        self._captcha_image = page.locator("img.valid-img")
        # Loading 遮罩（Element UI 全屏加载）
        self._loading_mask = page.locator(".el-loading-mask")
        # 记录登录页的 URL，用于判断是否跳转
        self._login_url = ""

    def navigate(self, url: str):
        """打开登录页面并等待验证码加载"""
        super().navigate(url)
        self.wait_for_visible(self._captcha_image)
        self._login_url = self.page.url

    def _get_captcha_text(self) -> str:
        """识别验证码图片并返回文本"""
        try:
            image_bytes = self._captcha_image.screenshot(type="png")
            captcha_text = recognize_from_bytes(image_bytes)
            return captcha_text.strip()
        except Exception as e:
            logger.warning(f"验证码识别失败: {e}")
            return ""

    def login(self, username: str, password: str, captcha: str):
        """使用指定验证码执行登录操作"""
        self.click_and_fill(self._username_input, username)
        self.click_and_fill(self._password_input, password)
        self.click_and_fill(self._captcha_input, captcha)
        self.click(self._login_button)

    def login_until_success(self, username: str, password: str) -> bool:
        """自动识别验证码并登录，失败则刷新重试直到成功"""
        for attempt in range(1, self.MAX_RETRY + 1):
            captcha = self._get_captcha_text()
            logger.info(f"第 {attempt} 次尝试，验证码识别结果: {captcha}")

            self.login(username, password, captcha)

            # 等待登录结果：URL跳转=成功，错误提示=失败
            success = self._wait_for_login_result(timeout=5000)
            if success:
                logger.info(f"第 {attempt} 次尝试登录成功！当前 URL: {self.page.url}")
                return True

            # 记录失败原因
            error_msg = self._get_error_message()
            logger.warning(f"第 {attempt} 次登录失败，提示: {error_msg}，刷新重试...")
            # 重试失败时截图保存，方便排查
            self.screenshot(f"登录重试第{attempt}次失败")
            # 等待 Loading 遮罩消失后再操作
            self._wait_for_loading_gone()
            self._captcha_image.click()
            # 等待验证码刷新完成
            self._wait_for_captcha_refreshed()

        logger.error(f"连续 {self.MAX_RETRY} 次登录失败，请检查验证码识别准确率")
        return False

    def _wait_for_login_result(self, timeout: int = 8000) -> bool:
        """点击登录后等待结果：URL跳转=成功，错误提示出现=失败"""
        interval = 300
        elapsed = 0
        while elapsed < timeout:
            if self._is_login_success():
                return True
            if self._is_loading_visible():
                self.page.wait_for_timeout(interval)
                elapsed += interval
                continue
            if self._is_error_message_visible():
                return False
            self.page.wait_for_timeout(interval)
            elapsed += interval
        return False

    def _is_loading_visible(self) -> bool:
        try:
            return self._loading_mask.is_visible()
        except Exception:
            return False

    def _is_error_message_visible(self) -> bool:
        try:
            if not self._message_paragraph.is_visible():
                return False
            text = self._message_paragraph.inner_text()
            if text.strip().lower() == "loading":
                return False
            return True
        except Exception:
            return False

    def _wait_for_loading_gone(self):
        try:
            self._loading_mask.wait_for(state="hidden", timeout=5000)
        except Exception:
            pass

    def _wait_for_captcha_refreshed(self):
        try:
            self._captcha_image.wait_for(state="visible", timeout=3000)
            self.page.wait_for_timeout(500)
        except Exception as e:
            logger.warning(f"等待验证码刷新异常: {e}")

    def _is_login_success(self) -> bool:
        current_url = self.page.url
        if self.LOGIN_URL_KEYWORD not in current_url and current_url != self._login_url:
            return True
        return False

    def _get_error_message(self) -> str:
        try:
            if not self._message_paragraph.is_visible():
                return "(未获取到提示)"
            text = self._message_paragraph.inner_text()
            if text.strip().lower() == "loading":
                return "(Loading中，未获取到错误提示)"
            return text
        except Exception:
            return "(未获取到提示)"

    def get_message_text(self) -> str:
        return self.get_text(self._message_paragraph)

    def assert_message_contains(self, expected_text: str):
        self.assert_text_contains(self._message_paragraph, expected_text)