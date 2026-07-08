"""JAKA 官网登录页面对象

JAKA 官网（Nuxt.js）登录流程：
  1. 打开首页，点击"登录"入口
  2. 切换到"密码登录"标签
  3. 填写手机号/邮箱 + 密码
  4. 勾选用户协议复选框
  5. 点击登录按钮
  6. 登录成功判断：页面出现"退出登录"
"""

from playwright.sync_api import Page

from common.logger import logger
from pages.base_page import BasePage


class JakaLoginPage(BasePage):
    """JAKA 官网登录页面对象"""

    def __init__(self, page: Page):
        super().__init__(page)
        # 首页"登录"入口
        self._login_entry = page.get_by_text("登录", exact=True)
        # "密码登录"标签 - 用 CSS 类选择器精确定位，避免 get_by_text 匹配到祖先元素
        self._password_login_tab = page.locator(".tab .item.f_16", has_text="密码登录")
        # 手机/邮箱输入框
        self._username_input = page.get_by_placeholder("请输入您的注册手机或者邮箱")
        # 密码输入框（仅在"密码登录"标签激活后才出现）
        self._password_input = page.get_by_placeholder("请输入您的密码")
        # 用户协议复选框 - 限定在登录弹窗范围内（页面有多个 #comm）
        self._agree_checkbox = page.locator(".login #comm")
        # 登录按钮 - 使用 class 精确定位
        self._login_button = page.locator(".login .submit")
        # 登录成功标志：退出登录
        self._logout_text = page.get_by_text("退出登录")

    def navigate(self, url: str):
        """打开 JAKA 官网首页并等待登录入口加载"""
        super().navigate(url)
        self.wait_for_visible(self._login_entry)
        logger.info(f"JAKA 官网首页加载完成，URL: {self.page.url}")

    def login(self, username: str, password: str):
        """执行完整登录流程：打开弹窗 → 切换密码登录 → 填写 → 勾选协议 → 点击登录"""
        # 点击首页"登录"入口，打开登录弹窗
        logger.info("点击首页登录入口")
        self.click(self._login_entry)
        # 等待登录弹窗渲染完成（Vue.js 需要时间挂载事件处理器）
        self.page.locator(".login .inner").wait_for(state="visible", timeout=self.timeout)
        self.page.wait_for_timeout(500)
        # 切换到密码登录标签（Vue.js 事件处理器可能未就绪，需重试）
        self._switch_to_password_login()
        # 填写手机号/邮箱
        logger.info(f"填写手机号/邮箱: {username}")
        self.click_and_fill(self._username_input, username)
        # 填写密码
        logger.info("填写密码")
        self.click_and_fill(self._password_input, password)
        # 勾选用户协议
        logger.info("勾选用户协议复选框")
        self._agree_checkbox.check(timeout=self.timeout)
        # 点击登录
        logger.info("点击登录按钮")
        self.click(self._login_button)

    def _switch_to_password_login(self, max_retries: int = 3):
        """切换到密码登录标签，通过检测密码输入框是否出现来确认切换成功

        Vue.js 弹窗渲染后事件处理器可能尚未挂载，首次点击可能无效，
        因此采用重试机制：点击后检测密码输入框是否出现，未出现则等待后重试。
        """
        for attempt in range(1, max_retries + 1):
            logger.info(f"切换到密码登录 (尝试 {attempt}/{max_retries})")
            self.click(self._password_login_tab)
            try:
                self._password_input.wait_for(state="visible", timeout=3000)
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

    def login_until_success(self, username: str, password: str) -> bool:
        """执行登录并等待成功

        JAKA 官网无验证码，直接登录，等待"退出登录"出现即为成功。

        Returns:
            True 表示登录成功，False 表示超时失败
        """
        self.login(username, password)
        return self._wait_for_login_result()

    def _wait_for_login_result(self, timeout: int = 15000) -> bool:
        """等待登录结果：页面出现"退出登录"即成功，超时即失败"""
        try:
            self._logout_text.wait_for(state="visible", timeout=timeout)
            logger.info("登录成功，已检测到'退出登录'")
            return True
        except Exception as e:
            logger.error(f"等待'退出登录'超时，登录失败: {e}")
            return False
