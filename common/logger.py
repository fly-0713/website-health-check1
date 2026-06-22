"""公共日志模块

提供统一的日志配置，支持控制台输出 + 文件输出。
用法：
    from common.logger import logger
    logger.info("信息")
    logger.warning("警告")
    logger.error("错误")
"""

import logging
import os
from datetime import datetime

# 日志根目录
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")

# 日志格式
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# 日志记录缓冲区（用于按用例附加 allure 日志）
_log_buffer: list = []
_current_case: str = ""


class CaseLogHandler(logging.Handler):
    """按用例缓冲日志，支持 allure 按用例附加"""

    def emit(self, record):
        _log_buffer.append(self.format(record))


def get_case_log() -> str:
    """获取当前用例的日志文本"""
    return "\n".join(_log_buffer)


def clear_case_log():
    """清空用例日志缓冲"""
    _log_buffer.clear()


def _create_logger(name: str = "ui_test") -> logging.Logger:
    """创建并配置 logger 实例

    - 控制台输出：INFO 及以上级别
    - 文件输出：DEBUG 及以上级别，按日期命名
    - 用例缓冲：记录每条日志，供 allure 附加
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    log = logging.getLogger(name)

    # 清理旧 handler（清理 logs 目录后重建时需要）
    log.handlers.clear()

    log.setLevel(logging.DEBUG)

    # --- 控制台 Handler ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    log.addHandler(console_handler)

    # --- 文件 Handler ---
    log_filename = f"test_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(
        os.path.join(LOG_DIR, log_filename),
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    log.addHandler(file_handler)

    # --- 用例缓冲 Handler ---
    case_handler = CaseLogHandler()
    case_handler.setLevel(logging.DEBUG)
    case_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    log.addHandler(case_handler)

    return log


# 全局 logger 实例
logger = _create_logger()
