"""工具函数模块

包含通用的工具函数，如类型映射、字符串处理等
"""

from typing import Dict, Any, Optional
import re
import logging

logger = logging.getLogger(__name__)

# MySQL类型到Python类型的映射
MYSQL_TYPE_MAPPING = {
    'int': 'int',
    'integer': 'int',
    'bigint': 'int',
    'tinyint': 'int',
    'smallint': 'int',
    'mediumint': 'int',
    'varchar': 'str',
    'char': 'str',
    'text': 'str',
    'longtext': 'str',
    'mediumtext': 'str',
    'tinytext': 'str',
    'float': 'float',
    'double': 'float',
    'decimal': 'Decimal',
    'numeric': 'Decimal',
    'datetime': 'datetime',
    'timestamp': 'datetime',
    'date': 'date',
    'time': 'time',
    'boolean': 'bool',
    'bool': 'bool',
    'json': 'Dict[str, Any]',
    'enum': 'str',
    'set': 'str',
}

# 需要导入的类型
TYPE_IMPORTS = {
    'Decimal': 'from decimal import Decimal',
    'datetime': 'from datetime import datetime',
    'date': 'from datetime import date',
    'time': 'from datetime import time',
    'Dict': 'from typing import Dict',
    'List': 'from typing import List',
    'Optional': 'from typing import Optional',
    'Any': 'from typing import Any',
}

def map_mysql_to_python_type(mysql_type: str, is_nullable: bool = True,
                            default_value: Optional[str] = None) -> str:
    """
    将MySQL类型映射为Python类型

    Args:
        mysql_type: MySQL字段类型
        is_nullable: 是否可为空
        default_value: 默认值

    Returns:
        Python类型字符串
    """
    # 提取基础类型（去掉长度限制等）
    base_type = re.split(r'[\(|,]', mysql_type)[0].lower()

    # 处理特殊情况
    if 'unsigned' in mysql_type.lower():
        base_type = base_type.replace(' unsigned', '')

    # 映射到Python类型
    python_type = MYSQL_TYPE_MAPPING.get(base_type, 'str')

    # 处理可空类型
    if is_nullable and python_type in ['int', 'float', 'bool', 'datetime', 'date', 'time', 'Decimal']:
        python_type = f'Optional[{python_type}]'

    return python_type

def get_type_imports(python_types: list) -> set:
    """
    获取需要导入的类型语句

    Args:
        python_types: Python类型列表

    Returns:
        需要导入的语句集合
    """
    imports = set()

    for type_str in python_types:
        # 从Optional[T]中提取T
        match = re.match(r'Optional\[(\w+)\]', type_str)
        if match:
            type_name = match.group(1)
        else:
            # 从Dict[K, V]中提取
            match = re.match(r'(\w+)\[', type_str)
            if match:
                type_name = match.group(1)
            else:
                type_name = type_str

        if type_name in TYPE_IMPORTS:
            imports.add(TYPE_IMPORTS[type_name])

    return imports

def camel_case_to_snake_case(name: str) -> str:
    """
    将驼峰命名转换为下划线命名

    Args:
        name: 驼峰命名字符串

    Returns:
        下划线命名字符串
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def snake_case_to_camel_case(name: str) -> str:
    """
    将下划线命名转换为驼峰命名

    Args:
        name: 下划线命名字符串

    Returns:
        驼峰命名字符串
    """
    components = name.split('_')
    return ''.join(x.title() for x in components)

def pascal_case(name: str) -> str:
    """
    将字符串转换为帕斯卡命名法（首字母大写的驼峰命名）

    Args:
        name: 输入字符串

    Returns:
        帕斯卡命名法字符串
    """
    return snake_case_to_camel_case(name)

def get_default_value_for_type(python_type: str, mysql_default: Optional[str] = None) -> str:
    """
    根据Python类型获取合适的默认值

    Args:
        python_type: Python类型字符串
        mysql_default: MySQL默认值

    Returns:
        默认值字符串
    """
    if mysql_default is not None and mysql_default.lower() != 'null':
        if mysql_default.lower() in ('current_timestamp', 'now()'):
            if 'datetime' in python_type:
                return 'None'  # datetime字段默认为None，由数据库处理
            return mysql_default

        # 处理数字类型
        if python_type in ['int', 'float'] or python_type.startswith('Optional['):
            try:
                return mysql_default
            except ValueError:
                pass

        # 处理字符串
        if python_type in ['str'] or python_type.startswith('Optional[str'):
            return f'"{mysql_default}"'

        # 处理布尔值
        if python_type in ['bool'] or python_type.startswith('Optional[bool'):
            if mysql_default.lower() in ('1', 'true', 'yes'):
                return 'True'
            elif mysql_default.lower() in ('0', 'false', 'no'):
                return 'False'

    # 根据类型提供默认值
    if python_type.startswith('Optional['):
        return 'None'
    elif python_type == 'str':
        return '""'
    elif python_type == 'int':
        return '0'
    elif python_type == 'float':
        return '0.0'
    elif python_type == 'bool':
        return 'False'
    elif python_type == 'Decimal':
        return 'Decimal("0")'
    elif python_type in ['datetime', 'date', 'time']:
        return 'None'
    elif python_type.startswith('Dict['):
        return 'dict()'
    elif python_type.startswith('List['):
        return 'list()'
    else:
        return 'None'

def validate_table_name(table_name: str) -> bool:
    """
    验证表名是否有效

    Args:
        table_name: 表名

    Returns:
        是否有效
    """
    if not table_name:
        return False

    # 表名不能以数字开头，只能包含字母、数字、下划线
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return bool(re.match(pattern, table_name))

def format_comment(comment: Optional[str]) -> str:
    """
    格式化注释字符串

    Args:
        comment: 原始注释

    Returns:
        格式化后的注释
    """
    if not comment:
        return ""

    # 清理注释中的特殊字符
    comment = comment.strip().replace('\n', ' ')
    comment = re.sub(r'\s+', ' ', comment)  # 合并多个空格

    return comment

def safe_class_name(table_name: str) -> str:
    """
    将表名转换为安全的类名

    Args:
        table_name: 表名

    Returns:
        安全的类名
    """
    # 移除表名前缀（如果有）
    if table_name.startswith('tbl_'):
        table_name = table_name[4:]
    elif table_name.startswith('tb_'):
        table_name = table_name[3:]

    # 转换为单数形式（简单的处理方式）
    if table_name.endswith('s') and len(table_name) > 1:
        # 简单的单数化处理
        table_name = table_name[:-1]

    # 转换为帕斯卡命名
    class_name = pascal_case(table_name)

    # 确保类名有效
    if not class_name[0].isalpha():
        class_name = f'Model{class_name}'

    return class_name

def escape_string(value: str) -> str:
    """
    转义字符串中的特殊字符

    Args:
        value: 原始字符串

    Returns:
        转义后的字符串
    """
    return value.replace('"', '\\"').replace("'", "\\'").replace('\n', '\\n')