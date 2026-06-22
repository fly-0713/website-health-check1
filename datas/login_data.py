"""登录模块测试数据

账号信息从 config.yaml 读取，此处只定义用例名称。
"""

from common.config import config

login_data = [
    {
        "case_name": "自动识别验证码登录",
        "username": config.get_account(0)["username"],
        "password": config.get_account(0)["password"],
    },
]
