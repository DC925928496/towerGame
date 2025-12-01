"""模板引擎

负责使用Jinja2模板引擎生成Python代码
"""

import os
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import logging
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound, TemplateError

from .config_manager import ConfigManager
from .utils import get_type_imports, safe_class_name, escape_string

logger = logging.getLogger(__name__)

class TemplateEngine:
    """模板引擎"""

    def __init__(self, config: ConfigManager):
        """
        初始化模板引擎

        Args:
            config: 配置管理器
        """
        self.config = config
        self.env = None
        self._setup_environment()

    def _setup_environment(self):
        """设置Jinja2环境"""
        try:
            # 设置模板目录
            template_dir = Path(self.config.config.template.template_dir)

            # 如果模板目录不存在，使用内置模板
            if not template_dir.exists():
                logger.warning(f"Template directory {template_dir} not found, using built-in templates")
                template_dir = Path(__file__).parent / "templates"

            # 创建Jinja2环境
            self.env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
                keep_trailing_newline=True
            )

            # 添加自定义过滤器
            self._add_custom_filters()

            logger.info(f"Template engine initialized with template directory: {template_dir}")

        except Exception as e:
            logger.error(f"Failed to initialize template engine: {e}")
            raise

    def _add_custom_filters(self):
        """添加自定义过滤器"""
        def safe_class_filter(value: str) -> str:
            """安全的类名过滤器"""
            return safe_class_name(value)

        def camel_case_filter(value: str) -> str:
            """驼峰命名过滤器"""
            return ''.join(word.title() for word in value.split('_'))

        def snake_case_filter(value: str) -> str:
            """下划线命名过滤器"""
            import re
            s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', value)
            return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        def escape_string_filter(value: str) -> str:
            """字符串转义过滤器"""
            return escape_string(value or "")

        def format_type_filter(value: str) -> str:
            """格式化类型过滤器"""
            # 移除Optional包装，用于类型导入检测
            if value.startswith('Optional[') and value.endswith(']'):
                return value[9:-1]
            return value

        # 注册过滤器
        self.env.filters['safe_class'] = safe_class_filter
        self.env.filters['camel_case'] = camel_case_filter
        self.env.filters['snake_case'] = snake_case_filter
        self.env.filters['escape_string'] = escape_string_filter
        self.env.filters['format_type'] = format_type_filter

    def render_entity_template(self, table_metadata: 'TableMetadata') -> str:
        """
        渲染实体类模板

        Args:
            table_metadata: 表元数据

        Returns:
            生成的Python代码字符串
        """
        try:
            # 准备模板上下文
            context = self._prepare_entity_context(table_metadata)

            # 加载模板
            template = self.env.get_template(self.config.config.template.entity_template)

            # 渲染模板
            rendered = template.render(**context)

            logger.debug(f"Successfully rendered entity template for table: {table_metadata.name}")
            return rendered

        except TemplateNotFound as e:
            logger.error(f"Template not found: {e}")
            # 使用内置简单模板
            return self._render_simple_entity_template(table_metadata)
        except TemplateError as e:
            logger.error(f"Template rendering error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error rendering template: {e}")
            raise

    def _render_simple_entity_template(self, table_metadata: 'TableMetadata') -> str:
        """使用内置简单模板渲染实体类"""
        context = self._prepare_entity_context(table_metadata)

        template_str = '''"""
自动生成的实体类文件
生成时间: {{ generation_time }}
工具版本: {{ tool_version }}
数据库版本: {{ database_version }}
警告: 此文件由工具自动生成，请勿手动修改！
"""

{% for import_line in imports %}
{{ import_line }}
{% endfor %}

@dataclass
class {{ class_name }}({{ base_class }}):
    """{{ class_comment }}"""

{% for column in columns %}
    {{ column.name }}: {{ column.python_type }}{% if not column.is_nullable %} = {{ column.default_value }}{% endif %}
{% endfor %}

{% if include_foreign_keys and foreign_keys %}
    # 外键关系
{% for fk in foreign_keys %}
    {{ fk.property_name }}: Optional['{{ fk.referenced_class }}'] = None
{% endfor %}
{% endif %}

    # 用户自定义方法保护区域
    # === USER_CUSTOM_METHODS_START ===
    # 用户可以在这里添加自定义方法，此区域不会被覆盖
    # === USER_CUSTOM_METHODS_END ===

{% if include_validation %}
    def validate(self) -> List[str]:
        """字段验证逻辑"""
        errors = []
{% for column in columns %}
{% if column.is_required %}
        if not {{ column.name }}:
            errors.append("{{ column.comment or column.name }}不能为空")
{% endif %}
{% endfor %}
        return errors
{% endif %}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> '{{ class_name }}':
        """从字典创建实例"""
        return cls(**data)
'''

        template = Template(template_str)
        return template.render(**context)

    def _prepare_entity_context(self, table_metadata: 'TableMetadata') -> Dict[str, Any]:
        """
        准备实体类模板的上下文数据

        Args:
            table_metadata: 表元数据

        Returns:
            模板上下文字典
        """
        # 获取所有需要的类型
        python_types = [col.python_type for col in table_metadata.columns]

        # 添加外键关系需要的类型
        if self.config.config.generation.include_foreign_keys:
            for fk in table_metadata.foreign_keys:
                referenced_class = safe_class_name(fk.referenced_table) + self.config.config.generation.suffix
                python_types.append(f"Optional['{referenced_class}']")

        # 获取类型导入
        type_imports = get_type_imports(python_types)

        # 构建导入语句列表
        imports = [
            "from dataclasses import dataclass",
            "from typing import List, Dict, Any, Optional",
        ]

        if 'Decimal' in python_types:
            imports.append("from decimal import Decimal")

        if any('datetime' in t for t in python_types):
            imports.append("from datetime import datetime")

        if any('date' in t for t in python_types):
            imports.append("from datetime import date")

        if any('time' in t for t in python_types):
            imports.append("from datetime import time")

        # 准备外键信息
        foreign_keys = []
        if self.config.config.generation.include_foreign_keys:
            for fk in table_metadata.foreign_keys:
                fk_info = {
                    'name': fk.name,
                    'column': fk.column,
                    'referenced_table': fk.referenced_table,
                    'referenced_column': fk.referenced_column,
                    'referenced_class': fk.referenced_class,  # 使用ForeignKeyMetadata的新方法
                    'property_name': fk.property_name,  # 使用ForeignKeyMetadata的新方法
                    'on_delete': fk.on_delete,
                    'on_update': fk.on_update,
                    'is_cascade_delete': fk.is_cascade_delete(),
                    'is_cascade_update': fk.is_cascade_update(),
                }
                foreign_keys.append(fk_info)

        # 处理列信息
        columns = []
        validation_rules = table_metadata.get_validation_rules()

        for col in table_metadata.columns:
            col_info = {
                'name': col.name,
                'data_type': col.data_type,
                'python_type': col.python_type,
                'is_nullable': col.is_nullable,
                'default_value': col.default_value,
                'comment': col.comment,
                'is_required': col.is_required,
                'is_primary_key': col.is_primary_key,
                'is_auto_increment': col.is_auto_increment,
                'is_unique': col.is_unique,
                'max_length': col.max_length,
                'has_default': col.has_default,
                'validation_rules': validation_rules.get(col.name, []),
            }
            columns.append(col_info)

        context = {
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'tool_version': '2.0.0',  # 升级版本号
            'database_version': 'tower_game v2.2',
            'class_name': safe_class_name(table_metadata.name) + self.config.config.generation.suffix,
            'class_comment': table_metadata.comment or f"{table_metadata.name}实体模型",
            'table_name': table_metadata.name,
            'imports': imports,
            'columns': columns,
            'primary_keys': table_metadata.primary_keys,
            'foreign_keys': foreign_keys,
            'base_class': self.config.config.generation.base_class,
            'include_validation': self.config.config.generation.include_validation,
            'include_foreign_keys': self.config.config.generation.include_foreign_keys,
            'table_comment': table_metadata.comment,
            # 新增的增强信息
            'validation_rules': validation_rules,
            'table_metadata': table_metadata,  # 提供完整的表元数据供高级模板使用
            'has_relationships': len(table_metadata.foreign_keys) > 0,
            'relationship_tables': table_metadata.get_relationship_tables(),
            'foreign_key_columns': table_metadata.get_foreign_key_columns(),
        }

        return context

    def render_init_template(self, class_names: List[str]) -> str:
        """
        渲染__init__.py模板

        Args:
            class_names: 生成的类名列表

        Returns:
            生成的__init__.py内容
        """
        try:
            context = {
                'class_names': class_names,
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'tool_version': '1.0.0',
            }

            template = self.env.get_template(self.config.config.template.init_template)
            rendered = template.render(**context)

            logger.debug("Successfully rendered __init__.py template")
            return rendered

        except TemplateNotFound:
            # 使用内置简单模板
            return self._render_simple_init_template(class_names)
        except TemplateError as e:
            logger.error(f"Template rendering error: {e}")
            raise

    def _render_simple_init_template(self, class_names: List[str]) -> str:
        """使用内置简单模板渲染__init__.py"""
        imports = []
        for class_name in class_names:
            imports.append(f"from .{class_name.lower()} import {class_name}")

        return f'''"""
自动生成的包初始化文件
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
工具版本: 1.0.0
"""

{chr(10).join(imports)}

__all__ = [
{chr(10).join(f"    '{name}'" for name in class_names)}
]
'''

    def render_base_model_template(self) -> str:
        """
        渲染基础模型类模板

        Returns:
            生成的基础模型类代码
        """
        try:
            context = {
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'tool_version': '1.0.0',
            }

            template = self.env.get_template(self.config.config.template.base_template)
            rendered = template.render(**context)

            logger.debug("Successfully rendered base model template")
            return rendered

        except TemplateNotFound:
            # 使用内置简单模板
            return self._render_simple_base_model_template()
        except TemplateError as e:
            logger.error(f"Template rendering error: {e}")
            raise

    def _render_simple_base_model_template(self) -> str:
        """使用内置简���模板渲染基础模型类"""
        generation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        template_content = f"""
\"\"\"
基础模型类
生成时间: {generation_time}
工具版本: 1.0.0
\"\"\"

from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class BaseModel:
    \"\"\"基础模型类，提供通用的序列化和反序列化功能\"\"\"

    def to_dict(self) -> Dict[str, Any]:
        \"\"\"转换为字典\"\"\"
        result = {{}}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                if hasattr(value, 'to_dict'):
                    result[key] = value.to_dict()
                elif isinstance(value, list):
                    result[key] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in value]
                else:
                    result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        \"\"\"从字典创建实例\"\"\"
        return cls(**data)

    def __str__(self) -> str:
        \"\"\"字符串表示\"\"\"
        return f\"{{self.__class__.__name__}}({{self.to_dict()}})\"
"""

        return template_content