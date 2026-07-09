"""JAKA 官网登录页面对象

JAKA 官网登录流程：
  1. 打开首页（默认英文版）
  2. 切换语言到简体中文
  3. 点击"登录"入口
  4. 切换到"密码登录"标签
  5. 填写手机号/邮箱 + 密码
  6. 勾选用户协议复选框
  7. 点击登录按钮
  8. 登录成功判断：检查用户头像是否出现
"""

import time
from playwright.sync_api import Page

from common.logger import logger
from pages.base_page import BasePage


class JakaLoginPage(BasePage):
    """JAKA 官网登录页面对象"""

    def __init__(self, page: Page):
        super().__init__(page)
        # 语言切换按钮（英文版页面上的 "English"）
        self._lang_switch = page.locator(".lag, .lag .h_f_l6, .lag span:has-text('English')").first
        # 登录入口（中文版页面）
        self._login_entry = page.locator(".btn_box .btn:has-text('登录'), a.btn:has-text('登录')").first
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
        self._user_avatar = page.locator(
            ".user-name, .el-dropdown-link, .avatar, .username, "
            ".user-info, [class*='user'], .header .name, .login-user"
        ).first
        # 安全提醒弹窗
        self._security_reminder = page.get_by_text("安全提醒")
        # Cookie 弹窗相关
        self._cookie_accept_button = page.locator("button.cky-btn-accept").first

    def navigate(self, url: str):
        """打开 JAKA 官网首页并切换到中文版"""
        super().navigate(url, wait_until="domcontentloaded", timeout=60000)
        
        try:
            self.page.wait_for_load_state("networkidle", timeout=30000)
            logger.info("页面网络空闲，所有资源已加载")
        except Exception as e:
            logger.warning(f"等待 networkidle 超时，继续执行: {e}")
        
        self._handle_cookie_dialog()
        self._switch_to_chinese()
        
        # 🔥 等待登录入口可见
        try:
            self._login_entry.wait_for(state="visible", timeout=15000)
            logger.info("JAKA 官网中文版加载完成，登录入口可见")
        except Exception as e:
            logger.warning(f"登录入口未出现: {e}")
            self.page.screenshot(path="login_entry_not_found.png")
            raise
        
        self.page.wait_for_timeout(2000)
        self._handle_security_reminder_fast()
        self.page.wait_for_timeout(1000)
        logger.info("页面已完全稳定，可以执行操作")

    def _switch_to_chinese(self):
        """切换到简体中文 - 仅在非中文版时执行"""
        current_url = self.page.url
        if "/zh" in current_url:
            logger.info(f"当前已是中文版，无需切换: {current_url}")
            return
        
        logger.info(f"当前为非中文版: {current_url}，开始切换语言")
        
        try:
            logger.info("点击语言切换按钮")
            self._lang_switch.evaluate("element => element.click()")
            self.page.wait_for_timeout(2000)
            
            logger.info("选择简体中文")
            clicked = self.page.evaluate("""
                () => {
                    const spans = document.querySelectorAll('span.note');
                    for (let span of spans) {
                        if (span.textContent.trim() === '简体中文') {
                            const a = span.closest('a');
                            if (a) {
                                a.click();
                                return true;
                            }
                        }
                    }
                    return false;
                }
            """)
            
            if clicked:
                logger.info("已点击简体中文选项")
            else:
                logger.warning("未找到简体中文选项")
            
            self.page.wait_for_timeout(3000)
            logger.info(f"已切换到中文版，当前 URL: {self.page.url}")
            self.page.wait_for_load_state("domcontentloaded", timeout=30000)
            
        except Exception as e:
            logger.warning(f"切换语言失败: {e}")
            logger.info("尝试直接访问中文版 URL")
            self.page.goto("https://www.jaka.com/zh", wait_until="domcontentloaded")
            self.page.wait_for_timeout(3000)

    def _handle_cookie_dialog(self):
        """处理 Cookie 同意弹窗"""
        try:
            if self._cookie_accept_button.is_visible(timeout=3000):
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

    def login(self, username: str, password: str):
        """执行完整登录流程"""
        
        # 🔥 点击首页"登录"入口
        logger.info("点击首页登录入口")
        try:
            if not self._login_entry.is_visible(timeout=5000):
                logger.warning("登录入口不可见，尝试刷新页面")
                self.page.reload()
                self.page.wait_for_timeout(3000)
                self._handle_cookie_dialog()
                self.page.wait_for_timeout(1000)
            
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
        
        self.page.wait_for_timeout(1000)
        logger.info("等待登录弹窗出现...")
        
        dialog_found = False
        dialog_selectors = [
            ".login .inner",
            ".login-modal",
            "[class*='login-dialog']",
            "[class*='LoginDialog']",
            ".modal-content",
            ".dialog-login",
            ".el-dialog",
            ".el-dialog__wrapper"
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
            # 🔥 检查用户头像是否出现
            if self._user_avatar.is_visible(timeout=2000):
                logger.info("✅ 登录成功，已检测到用户头像")
                return True
            
            self.page.wait_for_timeout(1000)
        
        logger.error(f"等待登录成功超时")
        return False