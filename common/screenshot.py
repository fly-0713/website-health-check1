"""公共截图工具"""

import os
from datetime import datetime

from playwright.sync_api import Page

from common.logger import logger

# 截图根目录
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "screenshots")


def take_screenshot(page: Page, name: str):
    """截图并保存到 screenshots 目录，文件名自动加时间戳

    Args:
        page: Playwright Page 对象
        name: 截图标识名称（如用例名）
    """
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    page.screenshot(path=filepath)
    logger.info(f"截图已保存: {filepath}")
    return filepath
