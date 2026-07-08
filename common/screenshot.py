"""
截图工具模块
"""

import os
from datetime import datetime
from pathlib import Path

from playwright.sync_api import Page

from common.logger import logger


def take_screenshot(page: Page, name: str) -> str:
    """截取当前页面

    Args:
        page: Playwright Page 对象
        name: 截图名称（用于文件名）

    Returns:
        截图文件路径
    """
    # 确保截图目录存在
    screenshot_dir = Path("screenshots")
    screenshot_dir.mkdir(exist_ok=True)

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{timestamp}.png"
    filepath = screenshot_dir / filename

    try:
        # 🔥 截图时设置超时时间为 10 秒，避免卡死
        page.screenshot(
            path=str(filepath),
            timeout=10000,
            full_page=False  # 只截取当前视口，避免全屏截图耗时过长
        )
        logger.info(f"截图已保存: {filepath}")
        return str(filepath)
    except Exception as e:
        logger.warning(f"截图失败: {e}")
        # 尝试使用更短的超时时间再次截图
        try:
            page.screenshot(
                path=str(filepath),
                timeout=3000,
                full_page=False
            )
            logger.info(f"截图已保存（重试）: {filepath}")
            return str(filepath)
        except Exception as e2:
            logger.warning(f"重试截图仍然失败: {e2}")
            # 返回空字符串，避免后续处理报错
            return ""