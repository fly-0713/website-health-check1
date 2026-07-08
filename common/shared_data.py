"""共享数据文件存储工具

将测试数据写入 JSON 文件，替代 shared_data 字典，
解耦测试用例之间的强依赖关系。

文件路径: datas/shared_data.json

使用方式:
    from common.shared_data import shared_data

    # 写入数据
    shared_data.set("serial_number", "TEST202606231327")
    shared_data.set("station_code", "CX000078-1")

    # 读取数据
    serial = shared_data.get("serial_number")
    station = shared_data.get("station_code", "默认值")
"""

import json
import os

from common.logger import logger

# 数据文件路径
_DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datas", "shared_data.json")


class SharedDataStore:
    """共享数据存储类"""

    def __init__(self, file_path: str = _DATA_FILE):
        self._file_path = file_path
        self._data = {}
        self._load()

    def _load(self):
        """从文件加载数据"""
        if os.path.exists(self._file_path):
            try:
                with open(self._file_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                logger.info(f"共享数据已从文件加载: {self._file_path}")
            except Exception as e:
                logger.warning(f"加载共享数据文件失败: {e}")
                self._data = {}
        else:
            self._data = {}

    def _save(self):
        """保存数据到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            logger.info(f"共享数据已保存到文件: {self._file_path}")
        except Exception as e:
            logger.error(f"保存共享数据文件失败: {e}")

    def set(self, key: str, value):
        """设置数据并保存到文件"""
        self._data[key] = value
        self._save()
        logger.info(f"共享数据写入: {key} = {value}")

    def get(self, key: str, default=None):
        """获取数据"""
        value = self._data.get(key, default)
        if value is None and default is None:
            logger.warning(f"共享数据未找到: {key}")
        return value

    def clear(self):
        """清空数据并删除文件"""
        self._data = {}
        if os.path.exists(self._file_path):
            os.remove(self._file_path)
            logger.info(f"共享数据文件已清空: {self._file_path}")

    def __getitem__(self, key: str):
        """支持 dict[key] 语法读取"""
        return self._data.get(key)

    def __setitem__(self, key: str, value):
        """支持 dict[key] = value 语法写入"""
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """支持 'key' in dict 语法"""
        return key in self._data


# 全局单例
shared_data = SharedDataStore()
