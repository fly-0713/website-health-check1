"""配置管理模块

从 config.yaml 读取环境配置，通过环境变量 ENV 切换环境。
用法：
    from common.config import config
    url = config.base_url
    headless = config.headless
"""

import os

import yaml


class Config:
    """配置对象，将 YAML 配置映射为属性"""

    def __init__(self, data: dict):
        self._data = data

    @property
    def base_url(self) -> str:
        return self._data.get("base_url", "")

    @property
    def headless(self) -> bool:
        return self._data.get("headless", False)

    @property
    def timeout(self) -> int:
        return self._data.get("timeout", 10000)

    @property
    def accounts(self) -> list:
        return self._data.get("accounts", [])

    def get_account(self, index: int = 0) -> dict:
        """获取指定索引的账号信息"""
        if index < len(self.accounts):
            return self.accounts[index]
        return {}


def load_config() -> Config:
    """加载配置文件，根据环境变量 ENV 选择环境"""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config.yaml",
    )

    with open(config_path, "r", encoding="utf-8") as f:
        all_config = yaml.safe_load(f)

    # 通过环境变量切换环境，默认 test
    env = os.environ.get("ENV", "test")
    env_config = all_config.get(env)
    if env_config is None:
        raise ValueError(f"未找到环境配置: {env}，可选: {list(all_config.keys())}")

    # 支持 CI 通过环境变量注入账号（覆盖 yaml 中的明文）
    ci_username = os.environ.get("TEST_USERNAME")
    ci_password = os.environ.get("TEST_PASSWORD")
    if ci_username and ci_password:
        env_config["accounts"] = [{"username": ci_username, "password": ci_password}]

    return Config(env_config)


# 全局配置实例
config = load_config()
