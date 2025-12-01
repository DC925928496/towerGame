"""
基础模型类
生成时间: 2025-11-30 08:31:29
工具版本: 1.0.0
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class BaseModel:
    """基础模型类，提供通用的序列化和反序列化功能"""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                if hasattr(value, "to_dict"):
                    result[key] = value.to_dict()
                elif isinstance(value, list):
                    result[key] = [
                        item.to_dict() if hasattr(item, "to_dict") else item
                        for item in value
                    ]
                else:
                    result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建实例"""
        return cls(**data)

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.__class__.__name__}({self.to_dict()})"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__()
