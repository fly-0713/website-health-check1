"""JAKA 官网登录页面对象

JAKA 官网（Nuxt.js）登录流程：
  1. 打开首页，关闭 Cookie 弹窗
  2. 检查是否已登录，如果已登录则跳过
  3. 点击"登录"入口
  4. 切换到"密码登录"标签
  5. 填写手机号/邮箱 + 密码
  6. 勾选用户协议复选框
  7. 点击登录按钮
  8. 登录成功判断：鼠标悬停用户头像展开下拉菜单，检测"退出登录"
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
        # 登录弹窗容器
        self._login_dialog = page.locator(".login .inner")
        # 🔥 用户头像/用户名 - 鼠标悬停展开下拉菜单
        self._user_avatar = page.locator(".user-name, .el-dropdown-link, .avatar, .username").first
        # 🔥 退出登录（在下拉菜单中）- 使用更精确的定位
        self._logout_text = page.locator("a.f_16:has-text('退出登录')").first
        # 安全提醒弹窗
        self._security_reminder = page.get_by_text("安全提醒")
        # Cookie 弹窗相关
        self._cookie_accept_button = page.locator("button.cky-btn-accept").first

    def navigate(self, url: str):
        """打开 JAKA 官网首页并等待页面加载"""
        super().navigate(url, wait_until="domcontentloaded", timeout=60000)
        self.page.wait_for_load_state("networkidle", timeout=30000)
        logger.info(f"JAKA 官网首页加载完成，URL: {self.page.url}")
        
        # 处理弹窗
        self._handle_all_dialogs()
        
        # 等待页面稳定
        self.page.wait_for_timeout(1000)

    def _handle_all_dialogs(self):
        """快速处理所有弹窗"""
        self._handle_cookie_dialog()
        self._handle_security_reminder_fast()

    def _handle_cookie_dialog(self):
        """处理 Cookie 同意弹窗"""
        try:
            if self._cookie_accept_button.is_visible(timeout=2000):
                logger.info("检测到 Cookie 弹窗，点击接受全部")
                self._cookie_accept_button.click()
                self.page.wait_for_timeout(500)
                logger.info("Cookie 弹窗已关闭")
        except Exception as e:
            logger.info(f"处理 Cookie 弹窗时出错（可忽略）: {e}")

    def _handle_security_reminder_fast(self):
        """快速处理安全提醒弹窗"""
        try:
            if self._security_reminder.is_visible(timeout=2000):
                logger.info("检测到安全提醒弹窗，使用 JavaScript 强制关闭")
                
                confirm_btn = self.page.locator(".confirm.btn:has-text('确定')").first
                if confirm_btn.is_visible(timeout=1000):
                    confirm_btn.evaluate("element => element.click()")
                    self.page.wait_for_timeout(500)
                    logger.info("安全提醒弹窗已关闭（点击确定）")
                    return
                
                logger.info("尝试使用 JavaScript 移除安全提醒弹窗")
                self.page.evaluate("""
                    () => {
                        const modal = document.querySelector('.el-dialog__wrapper, .el-message-box__wrapper, [class*="dialog"], [class*="modal"]');
                        if (modal) {
                            modal.style.display = 'none';
                            modal.parentNode?.removeChild(modal);
                        }
                        const mask = document.querySelector('.v-modal, .el-overlay');
                        if (mask) {
                            mask.style.display = 'none';
                        }
                    }
                """)
                self.page.wait_for_timeout(500)
                logger.info("已通过 JavaScript 移除安全提醒弹窗")
        except Exception as e:
            logger.info(f"处理安全提醒弹窗时出错（可忽略）: {e}")

    def _is_logged_in(self) -> bool:
        """检查当前是否已登录 - 鼠标悬停用户头像展开下拉菜单，检查退出登录"""
        try:
            # 1. 先检查用户头像是否存在
            if not self._user_avatar.is_visible(timeout=3000):
                logger.info("用户头像不可见，未登录")
                return False
            
            logger.info("检测到用户头像，鼠标悬停展开下拉菜单")
            
            # 2. 🔥 使用 hover 悬停展开下拉菜单（不是 click）
            self._user_avatar.hover()
            self.page.wait_for_timeout(500)
            
            # 3. 检查"退出登录"是否在下拉菜单中
            if self._logout_text.is_visible(timeout=3000):
                logger.info("✅ 检测到已登录状态（退出登录可见）")
                # 点击其他地方关闭下拉菜单
                self.page.mouse.click(0, 0)
                return True
            
            # 4. 点击其他地方关闭下拉菜单
            self.page.mouse.click(0, 0)
            return False
            
        except Exception as e:
            logger.info(f"检查登录状态时出错: {e}")
            return False

    def login(self, username: str, password: str):
        """执行完整登录流程"""
        
        # 检查是否已登录
        if self._is_logged_in():
            logger.info("✅ 已检测到登录状态，跳过登录流程")
            return
        
        # 点击首页"登录"入口
        logger.info("点击首页登录入口")
        self._login_entry.scroll_into_view_if_needed()
        self.page.wait_for_timeout(300)
        self._login_entry.evaluate("element => element.click()")
        
        # 等待登录弹窗出现
        logger.info("等待登录弹窗出现...")
        try:
            self._login_dialog.wait_for(state="visible", timeout=15000)
            logger.info("登录弹窗已出现")
        except Exception as e:
            logger.error(f"登录弹窗未出现: {e}")
            if self._is_logged_in():
                logger.info("虽然弹窗未出现，但检测到已登录状态，继续执行")
                return
            self.page.screenshot(path="login_dialog_not_found.png")
            raise
        
        self.page.wait_for_timeout(500)
        
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
            self.page.wait_for_timeout(300)
            
            try:
                self._password_input.wait_for(state="visible", timeout=5000)
                logger.info("密码登录标签已切换")
                return
            except Exception:
                if attempt < max_retries:
                    logger.warning("密码登录标签未切换，等待后重试...")
                    self.page.wait_for_timeout(800)
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
        """等待登录结果：鼠标悬停用户头像展开下拉菜单，检测到"退出登录"即成功"""
        start_time = self.page.evaluate("() => Date.now()")
        while self.page.evaluate("() => Date.now()") - start_time < timeout:
            if self._is_logged_in():
                logger.info("✅ 登录成功，已检测到'退出登录'")
                return True
            
            self.page.wait_for_timeout(1000)
        
        logger.error(f"等待登录成功超时")
        if self._is_logged_in():
            logger.info("虽然超时，但检测到已登录状态，视为成功")
            return True
        
        self.page.screenshot(path="login_timeout.png")
        return False