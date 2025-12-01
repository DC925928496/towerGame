"""
数据库实体类自动生成工具

该工具提供从MySQL数据库元数据自动生成Python实体类的功能。
支持PEP-484类型注解、增量更新、用户代码保护等功能。

作者: Claude
版本: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "Claude"

from .metadata_reader import DatabaseMetadataReader
from .entity_generator import EntityGenerator
from .config_manager import ConfigManager

__all__ = [
    "DatabaseMetadataReader",
    "EntityGenerator",
    "ConfigManager",
]