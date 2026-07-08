"""页面对象基类

所有 Page 对象继承 BasePage，封装通用操作（导航、点击、填入、等待、截图等）。
子类只需定义元素定位器和业务方法。
"""

from playwright.sync_api import Page, Locator, expect

from common.config import config
from common.logger import logger


class BasePage:
    """页面对象基类"""

    def __init__(self, page: Page):
        self.page = page
        self.timeout = config.timeout

    def navigate(self, url: str, wait_until: str = "load", timeout: int = None):
        """打开页面

        Args:
            url: 目标 URL
            wait_until: 页面加载完成条件，可选 load / domcontentloaded / networkidle / commit
            timeout: 导航超时时间（毫秒），默认使用 Playwright 全局 30 秒
        """
        logger.info(f"导航到: {url}")
        kwargs = {"wait_until": wait_until}
        if timeout is not None:
            kwargs["timeout"] = timeout
        self.page.goto(url, **kwargs)

    def click(self, locator: Locator):
        """点击元素"""
        locator.click(timeout=self.timeout)

    def fill(self, locator: Locator, value: str):
        """清空并填入文本"""
        locator.fill(value, timeout=self.timeout)

    def click_and_fill(self, locator: Locator, value: str):
        """点击后填入文本"""
        locator.click(timeout=self.timeout)
        locator.fill(value, timeout=self.timeout)

    def wait_for_visible(self, locator: Locator):
        """等待元素可见"""
        locator.wait_for(state="visible", timeout=self.timeout)

    def wait_for_hidden(self, locator: Locator):
        """等待元素隐藏"""
        locator.wait_for(state="hidden", timeout=self.timeout)

    def get_text(self, locator: Locator) -> str:
        """获取元素文本"""
        return locator.inner_text(timeout=self.timeout)

    def is_visible(self, locator: Locator) -> bool:
        """判断元素是否可见"""
        return locator.is_visible()

    def assert_text_contains(self, locator: Locator, expected: str):
        """断言元素文本包含指定内容"""
        expect(locator).to_contain_text(expected)

    def screenshot(self, name: str):
        """截取当前页面"""
        from common.screenshot import take_screenshot
        return take_screenshot(self.page, name)