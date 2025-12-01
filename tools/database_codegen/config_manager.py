"""配置管理模块

负责管理数据库连接配置和代码生成配置
"""

import os
import yaml
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """数据库连接配置"""
    host: str = "localhost"
    port: int = 3306
    database: str = ""
    user: str = ""
    password: str = ""
    charset: str = "utf8mb4"

@dataclass
class GenerationConfig:
    """代码生成配置"""
    output_dir: str = "./database/models"
    base_class: str = "BaseModel"
    include_validation: bool = True
    include_foreign_keys: bool = True
    include_indexes: bool = False
    custom_methods_protection: bool = True
    line_length: int = 88
    use_black: bool = True
    use_isort: bool = True
    include_comments: bool = True
    table_prefix: str = ""  # 表名前缀，生成类名时会去掉
    suffix: str = "Model"  # 类名后缀

@dataclass
class TemplateConfig:
    """模板配置"""
    template_dir: str = "./templates"
    entity_template: str = "entity.py.j2"
    init_template: str = "__init__.py.j2"
    base_template: str = "base_model.py.j2"

@dataclass
class CodegenConfig:
    """完整的代码生成配置"""
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    template: TemplateConfig = field(default_factory=TemplateConfig)
    excluded_tables: List[str] = field(default_factory=list)
    included_tables: Optional[List[str]] = None  # 如果指定，只生成这些表

class ConfigManager:
    """配置管理器"""

    DEFAULT_CONFIG_FILE = "codegen_config.yaml"
    DEFAULT_ENV_PREFIX = "CODEGEN_"

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，默认为当前目录下的codegen_config.yaml
        """
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.config = CodegenConfig()
        self._load_config()

    def _load_config(self):
        """加载配置"""
        # 1. 加载默认配置
        self._load_default_config()

        # 2. 从环境变量加载配置
        self._load_from_env()

        # 3. 从配置文件加载配置
        if os.path.exists(self.config_file):
            self._load_from_file()

        # 4. 验证配置
        self._validate_config()

    def _load_default_config(self):
        """加载默认配置"""
        # 默认配置已经在CodegenConfig的dataclass定义中
        pass

    def _load_from_env(self):
        """从环境变量加载配置"""
        env_mappings = {
            f"{self.DEFAULT_ENV_PREFIX}DB_HOST": ("database", "host"),
            f"{self.DEFAULT_ENV_PREFIX}DB_PORT": ("database", "port"),
            f"{self.DEFAULT_ENV_PREFIX}DB_NAME": ("database", "database"),
            f"{self.DEFAULT_ENV_PREFIX}DB_USER": ("database", "user"),
            f"{self.DEFAULT_ENV_PREFIX}DB_PASSWORD": ("database", "password"),
            f"{self.DEFAULT_ENV_PREFIX}DB_CHARSET": ("database", "charset"),
            f"{self.DEFAULT_ENV_PREFIX}OUTPUT_DIR": ("generation", "output_dir"),
            f"{self.DEFAULT_ENV_PREFIX}BASE_CLASS": ("generation", "base_class"),
            f"{self.DEFAULT_ENV_PREFIX}LINE_LENGTH": ("generation", "line_length"),
            f"{self.DEFAULT_ENV_PREFIX}USE_BLACK": ("generation", "use_black"),
            f"{self.DEFAULT_ENV_PREFIX}USE_ISORT": ("generation", "use_isort"),
            f"{self.DEFAULT_ENV_PREFIX}EXCLUDED_TABLES": ("excluded_tables", "list"),
        }

        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    if key == "port" or key == "line_length":
                        value = int(value)
                    elif key == "use_black" or key == "use_isort":
                        value = value.lower() in ('true', '1', 'yes', 'on')
                    elif key == "list":
                        value = [table.strip() for table in value.split(',') if table.strip()]
                    else:
                        value = str(value)

                    setattr(getattr(self.config, section), key, value)
                    logger.debug(f"Loaded config from env: {section}.{key} = {value}")
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to load config from env {env_var}: {e}")

    def _load_from_file(self):
        """从配置文件加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data:
                return

            # 加载数据库配置
            if 'database' in data:
                for key, value in data['database'].items():
                    if hasattr(self.config.database, key):
                        setattr(self.config.database, key, value)

            # 加载生成配置
            if 'generation' in data:
                for key, value in data['generation'].items():
                    if hasattr(self.config.generation, key):
                        setattr(self.config.generation, key, value)

            # 加载模板配置
            if 'template' in data:
                for key, value in data['template'].items():
                    if hasattr(self.config.template, key):
                        setattr(self.config.template, key, value)

            # 加载排除表列表
            if 'excluded_tables' in data:
                self.config.excluded_tables = data['excluded_tables']

            # 加载包含表列表
            if 'included_tables' in data:
                self.config.included_tables = data['included_tables']

            logger.info(f"Loaded configuration from {self.config_file}")

        except Exception as e:
            logger.error(f"Failed to load config file {self.config_file}: {e}")

    def _validate_config(self):
        """验证配置的有效性"""
        # 验证数据库配置
        if not self.config.database.database:
            logger.warning("Database name is not configured")

        if not self.config.database.user:
            logger.warning("Database user is not configured")

        # 验证输出目录
        output_dir = Path(self.config.generation.output_dir)
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Cannot create output directory {output_dir}: {e}")

        # 验证模板目录
        template_dir = Path(self.config.template.template_dir)
        if not template_dir.exists():
            logger.warning(f"Template directory {template_dir} does not exist")

    def get_database_url(self) -> str:
        """
        获取数据库连接URL

        Returns:
            数据库连接URL字符串
        """
        return (f"mysql://{self.config.database.user}:{self.config.database.password}@"
                f"{self.config.database.host}:{self.config.database.port}/"
                f"{self.config.database.database}?charset={self.config.database.charset}")

    def get_connection_params(self) -> Dict[str, Any]:
        """
        获取数据库连接参数

        Returns:
            数据库连接参数字典
        """
        return {
            'host': self.config.database.host,
            'port': self.config.database.port,
            'database': self.config.database.database,
            'user': self.config.database.user,
            'password': self.config.database.password,
            'charset': self.config.database.charset,
            'cursorclass': 'DictCursor',
        }

    def should_exclude_table(self, table_name: str) -> bool:
        """
        判断表是否应该被排除

        Args:
            table_name: 表名

        Returns:
            是否应该排除
        """
        # 如果有包含表列表，只处理在列表中的表
        if self.config.included_tables is not None:
            return table_name not in self.config.included_tables

        # 检查是否在排除列表中
        return table_name in self.config.excluded_tables

    def save_config(self, file_path: Optional[str] = None):
        """
        保存配置到文件

        Args:
            file_path: 配置文件路径，默认使用初始化时的路径
        """
        file_path = file_path or self.config_file

        config_dict = {
            'database': {
                'host': self.config.database.host,
                'port': self.config.database.port,
                'database': self.config.database.database,
                'user': self.config.database.user,
                'password': self.config.database.password,
                'charset': self.config.database.charset,
            },
            'generation': {
                'output_dir': self.config.generation.output_dir,
                'base_class': self.config.generation.base_class,
                'include_validation': self.config.generation.include_validation,
                'include_foreign_keys': self.config.generation.include_foreign_keys,
                'include_indexes': self.config.generation.include_indexes,
                'custom_methods_protection': self.config.generation.custom_methods_protection,
                'line_length': self.config.generation.line_length,
                'use_black': self.config.generation.use_black,
                'use_isort': self.config.generation.use_isort,
                'include_comments': self.config.generation.include_comments,
                'table_prefix': self.config.generation.table_prefix,
                'suffix': self.config.generation.suffix,
            },
            'template': {
                'template_dir': self.config.template.template_dir,
                'entity_template': self.config.template.entity_template,
                'init_template': self.config.template.init_template,
                'base_template': self.config.template.base_template,
            },
            'excluded_tables': self.config.excluded_tables,
        }

        if self.config.included_tables is not None:
            config_dict['included_tables'] = self.config.included_tables

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True, indent=2)

            logger.info(f"Configuration saved to {file_path}")

        except Exception as e:
            logger.error(f"Failed to save config file {file_path}: {e}")

    def __str__(self) -> str:
        """返回配置的字符串表示"""
        return f"CodegenConfig(database={self.config.database}, generation={self.config.generation})"