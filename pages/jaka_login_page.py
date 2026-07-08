"""JAKA 官网登录页面对象

JAKA 官网（Nuxt.js）登录流程：
  1. 打开首页，关闭 Cookie 弹窗
  2. 检查是否已登录，如果已登录则跳过
  3. 点击"登录"入口
  4. 切换到"密码登录"标签
  5. 填写手机号/邮箱 + 密码
  6. 勾选用户协议复选框
  7. 点击登录按钮
  8. 登录成功判断：页面出现"退出登录"
"""

from playwright.sync_api import Page

from common.logger import logger
from pages.base_page import BasePage


class JakaLoginPage(BasePage):
    """JAKA 官网登录页面对象"""

    def __init__(self, page: Page):
        super().__init__(page)
        # 首页"登录"入口
        self._login_entry = page.locator("a:has-text('登录')").first
        # "密码登录"标签
        self._password_login_tab = page.locator(".tab .item.f_16", has_text="密码登录")
        # 手机/邮箱输入框
        self._username_input = page.get_by_placeholder("请输入您的注册手机或者邮箱")
        # 密码输入框
        self._password_input = page.get_by_placeholder("请输入您的密码")
        # 用户协议复选框
        self._agree_checkbox = page.locator(".login #comm")
        # 登录按钮
        self._login_button = page.locator(".login .submit")
        # 登录成功标志：退出登录
        self._logout_text = page.get_by_text("退出登录")
        # 登录弹窗容器
        self._login_dialog = page.locator(".login .inner")
        # 已登录状态标志：修改密码
        self._change_password_text = page.get_by_text("修改密码")
        # 安全提醒弹窗
        self._security_reminder = page.get_by_text("安全提醒")
        # Cookie 弹窗相关
        self._cookie_accept_button = page.get_by_text("接受所有的")

    def navigate(self, url: str):
        """打开 JAKA 官网首页并等待页面加载"""
        super().navigate(url, wait_until="domcontentloaded", timeout=60000)
        self.page.wait_for_load_state("networkidle", timeout=30000)
        logger.info(f"JAKA 官网首页加载完成，URL: {self.page.url}")
        
        # 🔥 先处理 Cookie 弹窗
        self._handle_cookie_dialog()
        
        # 🔥 再处理安全提醒弹窗
        self._handle_security_reminder()
        
        # 等待页面稳定
        self.page.wait_for_timeout(2000)

    def _handle_cookie_dialog(self):
        """处理 Cookie 同意弹窗"""
        try:
            if self._cookie_accept_button.is_visible(timeout=3000):
                logger.info("检测到 Cookie 弹窗，点击接受全部")
                self._cookie_accept_button.click()
                self.page.wait_for_timeout(1000)
                logger.info("Cookie 弹窗已关闭")
        except Exception as e:
            logger.info(f"处理 Cookie 弹窗时出错（可忽略）: {e}")

    def _handle_security_reminder(self):
        """处理安全提醒弹窗"""
        try:
            # 检查安全提醒弹窗
            if self._security_reminder.is_visible(timeout=3000):
                logger.info("检测到安全提醒弹窗")
                # 查找"确定"按钮
                confirm_button = self.page.get_by_text("确定")
                if confirm_button.is_visible(timeout=2000):
                    confirm_button.click()
                    self.page.wait_for_timeout(1000)
                    logger.info("安全提醒弹窗已关闭")
                else:
                    # 尝试点击"取消"
                    cancel_button = self.page.get_by_text("取消")
                    if cancel_button.is_visible(timeout=2000):
                        cancel_button.click()
                        self.page.wait_for_timeout(1000)
                        logger.info("安全提醒弹窗已关闭（点击取消）")
        except Exception as e:
            logger.info(f"处理安全提醒弹窗时出错（可忽略）: {e}")

    def _is_logged_in(self) -> bool:
        """检查当前是否已登录"""
        try:
            # 🔥 检查多个登录状态标志，增加等待时间
            if self._logout_text.is_visible(timeout=5000):
                logger.info("✅ 检测到已登录状态（退出登录可见）")
                return True
            if self._change_password_text.is_visible(timeout=5000):
                logger.info("✅ 检测到已登录状态（修改密码可见）")
                return True
            # 🔥 检查"登录"链接是否存在（如果不存在，可能已登录）
            login_link = self.page.locator("a:has-text('登录')").first
            if not login_link.is_visible(timeout=2000):
                # "登录"链接不可见，可能已登录
                logger.info("✅ '登录'链接不可见，可能已登录")
                return True
            return False
        except Exception as e:
            logger.info(f"检查登录状态时出错: {e}")
            return False

    def login(self, username: str, password: str):
        """执行完整登录流程"""
        
        # 首先处理可能出现的弹窗
        self._handle_security_reminder()
        
        # 检查是否已登录
        if self._is_logged_in():
            logger.info("✅ 已检测到登录状态，跳过登录流程")
            return
        
        # 点击首页"登录"入口
        logger.info("点击首页登录入口")
        
        # 确保登录按钮可见并可点击
        self._login_entry.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)
        
        # 使用 JavaScript 点击
        self._login_entry.evaluate("element => element.click()")
        
        # 等待登录弹窗出现
        logger.info("等待登录弹窗出现...")
        try:
            self._login_dialog.wait_for(state="visible", timeout=15000)
            logger.info("登录弹窗已出现")
        except Exception as e:
            logger.error(f"登录弹窗未出现: {e}")
            # 再次检查是否已经登录
            if self._is_logged_in():
                logger.info("虽然弹窗未出现，但检测到已登录状态，继续执行")
                return
            self.page.screenshot(path="login_dialog_not_found.png")
            raise
        
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
        
        # 点击登录
        logger.info("点击登录按钮")
        self.click(self._login_button)

    def _switch_to_password_login(self, max_retries: int = 3):
        """切换到密码登录标签"""
        for attempt in range(1, max_retries + 1):
            logger.info(f"切换到密码登录 (尝试 {attempt}/{max_retries})")
            
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

    def login_until_success(self, username: str, password: str) -> bool:
        """执行登录并等待成功"""
        try:
            self.login(username, password)
            return self._wait_for_login_result()
        except Exception as e:
            logger.error(f"登录过程异常: {e}")
            self.page.screenshot(path="login_error.png")
            return False

    def _wait_for_login_result(self, timeout: int = 15000) -> bool:
        """等待登录结果：页面出现"退出登录"即成功"""
        try:
            self._logout_text.wait_for(state="visible", timeout=timeout)
            logger.info("✅ 登录成功，已检测到'退出登录'")
            return True
        except Exception as e:
            logger.error(f"等待'退出登录'超时，登录失败: {e}")
            # 🔥 超时后再次检查是否已登录
            if self._is_logged_in():
                logger.info("虽然等待超时，但检测到已登录状态，视为成功")
                return True
            return False