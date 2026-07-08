"""配置管理模块

从 config.yaml 读取环境配置，通过环境变量 ENV 切换环境。
用法：
    from common.config import config
    url = config.base_url
    headless = config.headless

注意：
    config 是懒加载单例，第一次访问属性时才真正读取 YAML。
    这允许 main.py 先设置 ENV 环境变量，再由 pytest 收集用例时加载配置。
"""

import os
import re
import yaml
from pathlib import Path


class Config:
    """配置管理类 - 支持环境变量替换"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """加载配置文件并替换环境变量"""
        config_path = Path(__file__).parent.parent / "config.yaml"

        with open(config_path, 'r', encoding='utf-8') as f:
            raw_config = yaml.safe_load(f)

        # 递归替换所有配置中的环境变量
        self._config = self._replace_env_vars(raw_config)

    def reload(self):
        """重新加载配置文件（供 main.py 在设置环境变量后调用）"""
        self._load_config()
    
    def _replace_env_vars(self, obj):
        """递归替换字符串中的 ${ENV_VAR} 格式的环境变量"""
        if isinstance(obj, str):
            # 匹配 ${VAR_NAME} 格式
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, obj)
            for var_name in matches:
                env_value = os.getenv(var_name, "")
                obj = obj.replace(f"${{{var_name}}}", env_value)
            return obj
        elif isinstance(obj, dict):
            return {k: self._replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._replace_env_vars(item) for item in obj]
        else:
            return obj
    
    # ========== MES 后台配置 ==========
    @property
    def mes_config(self):
        """获取 MES 后台完整配置"""
        return self._config.get("mes", {})
    
    @property
    def base_url(self):
        """MES 后台 URL"""
        return self.mes_config.get("base_url", "https://mes.jaka.com/")
    
    @property
    def headless(self):
        """MES 后台无头模式"""
        return self.mes_config.get("headless", False)
    
    @property
    def timeout(self):
        """MES 后台超时时间"""
        return self.mes_config.get("timeout", 10000)
    
    @property
    def accounts(self):
        """MES 后台账号列表"""
        return self.mes_config.get("accounts", [])
    
    def get_account(self, index=0):
        """获取 MES 后台指定索引的账号"""
        if self.accounts and len(self.accounts) > index:
            return self.accounts[index]
        return {"username": "", "password": ""}
    
    # ========== JAKA 官网配置 ==========
    @property
    def jaka_config(self):
        """获取 JAKA 官网完整配置"""
        return self._config.get("jaka_web", {})
    
    @property
    def jaka_base_url(self):
        """JAKA 官网 URL"""
        return self.jaka_config.get("base_url", "https://www.jaka.com/")
    
    @property
    def jaka_accounts(self):
        """JAKA 官网账号列表"""
        return self.jaka_config.get("accounts", [])
    
    def get_jaka_account(self, index=0):
        """获取 JAKA 官网指定索引的账号"""
        if self.jaka_accounts and len(self.jaka_accounts) > index:
            return self.jaka_accounts[index]
        return {"username": "", "password": ""}


# 单例实例
config = Config()