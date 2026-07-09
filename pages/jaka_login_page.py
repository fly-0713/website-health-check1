"""JAKA 官网登录页面对象

JAKA 官网（Nuxt.js）登录流程：
  1. 打开首页，关闭 Cookie 弹窗
  2. 检查是否已登录（通过用户头像判断）
  3. 如果已登录则跳过，否则执行登录流程
  4. 点击"登录"入口
  5. 切换到"密码登录"标签
  6. 填写手机号/邮箱 + 密码
  7. 勾选用户协议复选框
  8. 点击登录按钮
  9. 登录成功判断：检查用户头像是否出现
"""

import time
from playwright.sync_api import Page

from common.logger import logger
from pages.base_page import BasePage


class JakaLoginPage(BasePage):
    """JAKA 官网登录页面对象"""

    def __init__(self, page: Page):
        super().__init__(page)
        # 登录入口 - 支持多种元素类型
        self._login_entry = page.locator(
            "a:has-text('登录'), button:has-text('登录'), .login-btn, [class*='login'], [class*='Login']"
        ).first
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
        self._login_dialog = page.locator(".login .inner, .login-modal, [class*='login-dialog']").first
        # 登录成功标志：用户头像/用户名
        self._user_avatar = page.locator(".user-name, .el-dropdown-link, .avatar, .username").first
        # 安全提醒弹窗
        self._security_reminder = page.get_by_text("安全提醒")
        # Cookie 弹窗相关
        self._cookie_accept_button = page.locator("button.cky-btn-accept").first

    def navigate(self, url: str):
        """打开 JAKA 官网首页并等待页面加载"""
        super().navigate(url, wait_until="domcontentloaded", timeout=60000)
        
        self.page.wait_for_load_state("networkidle", timeout=30000)
        
        try:
            self._login_entry.wait_for(state="visible", timeout=15000)
            logger.info("JAKA 官网首页加载完成，登录入口可见")
        except Exception as e:
            logger.warning(f"登录入口未出现，尝试刷新页面: {e}")
            self.page.reload()
            self.page.wait_for_timeout(2000)
            self._login_entry.wait_for(state="visible", timeout=15000)
            logger.info("刷新后登录入口可见")
        
        self._handle_all_dialogs()
        self.page.wait_for_timeout(500)

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
        """检查当前是否已登录 - 只通过用户头像判断"""
        try:
            if self._user_avatar.is_visible(timeout=2000):
                logger.info("✅ 检测到已登录状态（用户头像可见）")
                return True
            return False
        except Exception as e:
            logger.info(f"检查登录状态时出错: {e}")
            return False

    def login(self, username: str, password: str):
        """执行完整登录流程"""
        
        if self._is_logged_in():
            logger.info("✅ 已检测到登录状态，跳过登录流程")
            return
        
        logger.info("点击首页登录入口")
        try:
            if not self._login_entry.is_visible(timeout=5000):
                logger.warning("登录入口不可见，尝试刷新页面")
                self.page.reload()
                self.page.wait_for_timeout(2000)
                self._handle_all_dialogs()
            
            self._login_entry.click(timeout=5000, force=True)
            logger.info("已通过 Playwright 点击登录入口")
        except Exception as e:
            logger.warning(f"原生点击失败: {e}")
            try:
                self._login_entry.evaluate("element => element.click()")
                logger.info("已通过 JavaScript 点击登录入口")
            except Exception as e2:
                logger.error(f"JavaScript 点击也失败: {e2}")
                raise
        
        logger.info("等待登录弹窗出现...")
        dialog_found = False
        
        dialog_selectors = [
            ".login .inner",
            ".login-modal",
            "[class*='login-dialog']",
            "[class*='LoginDialog']",
            ".modal-content",
            ".dialog-login"
        ]
        
        for selector in dialog_selectors:
            try:
                locator = self.page.locator(selector).first
                if locator.is_visible(timeout=2000):
                    self._login_dialog = locator
                    logger.info(f"登录弹窗已出现（选择器: {selector}）")
                    dialog_found = True
                    break
            except:
                pass
        
        if not dialog_found:
            try:
                self._login_dialog.wait_for(state="visible", timeout=15000)
                logger.info("登录弹窗已出现（原始选择器）")
                dialog_found = True
            except Exception as e:
                logger.error(f"登录弹窗未出现: {e}")
                if self._is_logged_in():
                    logger.info("虽然弹窗未出现，但检测到已登录状态，跳过登录流程")
                    return
                self.page.screenshot(path="login_dialog_not_found.png")
                raise
        
        self.page.wait_for_timeout(500)
        
        self._switch_to_password_login()
        
        logger.info(f"填写手机号/邮箱: {username}")
        self.click_and_fill(self._username_input, username)
        
        logger.info("填写密码")
        self.click_and_fill(self._password_input, password)
        
        logger.info("勾选用户协议复选框")
        try:
            self._agree_checkbox.check(timeout=self.timeout)
        except Exception as e:
            logger.warning(f"勾选协议失败，尝试点击: {e}")
            self._agree_checkbox.click()
        
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
        """等待登录结果：用户头像出现即成功"""
        start_time = time.time()
        while (time.time() - start_time) * 1000 < timeout:
            if self._is_logged_in():
                logger.info("✅ 登录成功，已检测到用户头像")
                return True
            
            self.page.wait_for_timeout(1000)
        
        logger.error(f"等待登录成功超时")
        if self._is_logged_in():
            logger.info("虽然超时，但检测到已登录状态，视为成功")
            return True
        
        # 🔥 截图超时改为 60 秒
        try:
            self.page.screenshot(path="login_timeout.png", timeout=60000)
        except Exception as e:
            logger.warning(f"超时截图失败: {e}")
        
        return False