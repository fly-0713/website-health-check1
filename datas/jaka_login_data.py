"""JAKA 官网登录模块测试数据

账号信息从 config.yaml 的 jaka_web 配置段读取，不依赖 ENV 切换。
CI 可通过环境变量 JAKA_WEB_USERNAME / JAKA_WEB_PASSWORD 注入。
"""

from common.config import config

jaka_login_data = [
    {
        "case_name": "JAKA官网正常登录",
        "base_url": config.jaka_web_base_url,
        "username": config.get_jaka_web_account(0)["username"],
        "password": config.get_jaka_web_account(0)["password"],
    },
]
