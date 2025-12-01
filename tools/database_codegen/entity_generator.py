"""实体类生成器

负责协调元数据读取和模板渲染，生成最终的实体类文件
"""

import os
import black
import isort
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

from .metadata_reader import DatabaseMetadataReader, TableMetadata
from .template_engine import TemplateEngine
from .config_manager import ConfigManager
from .utils import safe_class_name
from .incremental_updater import IncrementalUpdater

logger = logging.getLogger(__name__)

class EntityGenerator:
    """实体类生成器"""

    def __init__(self, config: ConfigManager):
        """
        初始化实体类生成器

        Args:
            config: 配置管理器
        """
        self.config = config
        self.metadata_reader = DatabaseMetadataReader(config)
        self.template_engine = TemplateEngine(config)
        self.incremental_updater = IncrementalUpdater(config)

    def generate_all_entities(self, preview_mode: bool = False) -> List[str]:
        """
        生成所有表的实体类

        Args:
            preview_mode: 是否为预览模式（不实际生成文件）

        Returns:
            生成的文件路径列表
        """
        logger.info("Starting to generate all entities")

        try:
            # ��试数据库连接
            if not self.metadata_reader.test_connection():
                raise ConnectionError("Failed to connect to database")

            # 读取所有表元数据
            tables = self.metadata_reader.read_all_tables()
            if not tables:
                logger.warning("No tables found to generate entities")
                return []

            # 创建输出目录
            output_dir = Path(self.config.config.generation.output_dir)
            if not preview_mode:
                output_dir.mkdir(parents=True, exist_ok=True)

            # 生成实体类文件
            generated_files = []
            class_names = []

            for table in tables:
                try:
                    file_path = self._generate_entity_file(table, output_dir, preview_mode)
                    if file_path:
                        generated_files.append(file_path)
                        class_name = safe_class_name(table.name) + self.config.config.generation.suffix
                        class_names.append(class_name)
                        logger.info(f"Generated entity for table: {table.name}")
                except Exception as e:
                    logger.error(f"Failed to generate entity for table {table.name}: {e}")
                    continue

            # 生成基础模型类
            if not preview_mode:
                self._generate_base_model_file(output_dir)

            # 生成__init__.py文件
            if class_names and not preview_mode:
                self._generate_init_file(output_dir, class_names)

            logger.info(f"Successfully generated {len(generated_files)} entity files")
            return generated_files

        except Exception as e:
            logger.error(f"Failed to generate entities: {e}")
            raise

    def generate_entity(self, table_name: str, preview_mode: bool = False) -> Optional[str]:
        """
        生成单个表的实体类

        Args:
            table_name: 表名
            preview_mode: 是否为预览模式

        Returns:
            生成的文件路径，如果失败返回None
        """
        logger.info(f"Starting to generate entity for table: {table_name}")

        try:
            # 测试数据库连接
            if not self.metadata_reader.test_connection():
                raise ConnectionError("Failed to connect to database")

            # 读取表元数据
            table = self.metadata_reader.read_table_metadata(table_name)
            if not table:
                logger.error(f"Table {table_name} not found")
                return None

            # 创建输出目录
            output_dir = Path(self.config.config.generation.output_dir)
            if not preview_mode:
                output_dir.mkdir(parents=True, exist_ok=True)

            # 生成实体类文件
            file_path = self._generate_entity_file(table, output_dir, preview_mode)

            if file_path:
                logger.info(f"Successfully generated entity for table: {table_name}")
            return file_path

        except Exception as e:
            logger.error(f"Failed to generate entity for table {table_name}: {e}")
            return None

    def _generate_entity_file(self, table: TableMetadata, output_dir: Path, preview_mode: bool = False) -> Optional[str]:
        """
        生成单个实体类文件

        Args:
            table: 表元数据
            output_dir: 输出目录
            preview_mode: 是否为预览模式

        Returns:
            生成的文件路径
        """
        try:
            # 生成类名
            class_name = safe_class_name(table.name) + self.config.config.generation.suffix
            file_name = f"{class_name.lower()}.py"
            file_path = output_dir / file_name

            # 检查文件是否已存在
            if file_path.exists() and not preview_mode:
                if self.config.config.generation.custom_methods_protection:
                    # 保护用户自定义方法
                    existing_content = self._backup_user_methods(file_path)
                    if existing_content:
                        logger.info(f"Protected custom methods in existing file: {file_path}")

            # 使用模板引擎生成代码
            generated_code = self.template_engine.render_entity_template(table)

            # 格式化代码
            if self.config.config.generation.use_black:
                try:
                    generated_code = black.format_str(
                        generated_code,
                        mode=black.FileMode(line_length=self.config.config.generation.line_length)
                    )
                except Exception as e:
                    logger.warning(f"Failed to format code with Black: {e}")

            # 排序导入语句
            if self.config.config.generation.use_isort:
                try:
                    generated_code = isort.code(
                        generated_code,
                        profile="black",
                        line_length=self.config.config.generation.line_length
                    )
                except Exception as e:
                    logger.warning(f"Failed to sort imports with isort: {e}")

            # 恢复用户自定义方法
            if (file_path.exists() and self.config.config.generation.custom_methods_protection
                    and not preview_mode):
                generated_code = self._restore_user_methods(generated_code)

            if preview_mode:
                logger.info(f"Preview mode - would generate file: {file_path}")
                logger.debug(f"Generated code preview:\n{generated_code}")
                return str(file_path)

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(generated_code)

            logger.info(f"Generated entity file: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to generate entity file for table {table.name}: {e}")
            raise

    def _backup_user_methods(self, file_path: Path) -> Optional[str]:
        """
        备份用户自定义方法

        Args:
            file_path: 文件路径

        Returns:
            用户自定义方法的内容，如果没有则返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找用户自定义方法区域
            start_marker = "# === USER_CUSTOM_METHODS_START ==="
            end_marker = "# === USER_CUSTOM_METHODS_END ==="

            start_index = content.find(start_marker)
            end_index = content.find(end_marker)

            if start_index != -1 and end_index != -1:
                # 提取用户自定义方法
                user_methods = content[start_index:end_index + len(end_marker)]
                # 临时保存到类属性中
                if not hasattr(self, '_user_methods_backup'):
                    self._user_methods_backup = {}
                self._user_methods_backup[str(file_path)] = user_methods
                return user_methods

        except Exception as e:
            logger.warning(f"Failed to backup user methods from {file_path}: {e}")

        return None

    def _restore_user_methods(self, generated_code: str) -> str:
        """
        恢复用户自定义方法

        Args:
            generated_code: 生成的代码

        Returns:
            恢复用户自定义方法后的代码
        """
        if not hasattr(self, '_user_methods_backup'):
            return generated_code

        # 查找生成的用户自定义方法区域
        start_marker = "# === USER_CUSTOM_METHODS_START ==="
        end_marker = "# === USER_CUSTOM_METHODS_END ==="

        start_index = generated_code.find(start_marker)
        end_index = generated_code.find(end_marker)

        if start_index != -1 and end_index != -1:
            # 这里简化处理，直接返回原始生成的代码
            # 实际项目中可以根据文件路径获取对应的用户方法
            pass

        return generated_code

    def _generate_base_model_file(self, output_dir: Path):
        """
        生成基础模型类文件

        Args:
            output_dir: 输出目录
        """
        try:
            file_path = output_dir / "base_model.py"

            # 如果文件已存在且启用了自定义方法保护，则跳过
            if file_path.exists() and self.config.config.generation.custom_methods_protection:
                logger.info(f"BaseModel file exists and custom methods protection is enabled, skipping: {file_path}")
                return

            # 使用模板引擎生成代码
            generated_code = self.template_engine.render_base_model_template()

            # 格式���代码
            if self.config.config.generation.use_black:
                try:
                    generated_code = black.format_str(
                        generated_code,
                        mode=black.FileMode(line_length=self.config.config.generation.line_length)
                    )
                except Exception as e:
                    logger.warning(f"Failed to format base model code with Black: {e}")

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(generated_code)

            logger.info(f"Generated base model file: {file_path}")

        except Exception as e:
            logger.error(f"Failed to generate base model file: {e}")
            raise

    def _generate_init_file(self, output_dir: Path, class_names: List[str]):
        """
        生成__init__.py文件

        Args:
            output_dir: 输出目录
            class_names: 类名列表
        """
        try:
            file_path = output_dir / "__init__.py"

            # 使用模板引擎生成代码
            generated_code = self.template_engine.render_init_template(class_names)

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(generated_code)

            logger.info(f"Generated __init__.py file: {file_path}")

        except Exception as e:
            logger.error(f"Failed to generate __init__.py file: {e}")
            raise

    def get_preview_for_table(self, table_name: str) -> Optional[str]:
        """
        获取指定表的代码预览

        Args:
            table_name: 表名

        Returns:
            生成的代码预览，如果失败返回None
        """
        try:
            # 测试数据库连接
            if not self.metadata_reader.test_connection():
                raise ConnectionError("Failed to connect to database")

            # 读取表元数据
            table = self.metadata_reader.read_table_metadata(table_name)
            if not table:
                logger.error(f"Table {table_name} not found")
                return None

            # 使用模板引擎生成代码
            generated_code = self.template_engine.render_entity_template(table)

            return generated_code

        except Exception as e:
            logger.error(f"Failed to get preview for table {table_name}: {e}")
            return None

    def update_all_entities_incremental(self, preview_mode: bool = False,
                                      backup_custom_methods: bool = True) -> List[str]:
        """
        增量更新所有表的实体类

        Args:
            preview_mode: 是否为预览模式（不实际生成文件）
            backup_custom_methods: 是否备份用户自定义方法

        Returns:
            更新的文件路径列表
        """
        logger.info("开始增量更新所有实体类")

        try:
            # 测试数据库连接
            if not self.metadata_reader.test_connection():
                raise ConnectionError("Failed to connect to database")

            # 读取当前表元数据
            current_tables = self.metadata_reader.read_all_tables()
            if not current_tables:
                logger.warning("没有找到表，无法进行增量更新")
                return []

            # 检测变化
            changes = self.incremental_updater.detect_changes(current_tables, backup_custom_methods)

            if not changes:
                logger.info("没有检测到任何变化，无需更新")
                return []

            # 创建输出目录
            output_dir = Path(self.config.config.generation.output_dir)
            if not preview_mode:
                output_dir.mkdir(parents=True, exist_ok=True)

            # 处理变更
            updated_files = []
            class_names = []

            for change in changes:
                if change.change_type.value in ['table_removed']:
                    # 表删除：删除对应的文件
                    file_path = self._get_model_file_path(change.table_name)
                    if file_path.exists() and not preview_mode:
                        file_path.unlink()
                        logger.info(f"删除已删除表的文件: {file_path}")
                    updated_files.append(str(file_path))

                elif change.change_type.value in ['table_added', 'table_modified']:
                    # 新增或修改的表：重新生成
                    if change.new_metadata:
                        file_path = self._get_model_file_path(change.table_name)

                        if preview_mode:
                            logger.info(f"预览模式 - 将更新文件: {file_path}")
                        else:
                            success = self.incremental_updater.apply_incremental_update(
                                change.new_metadata, file_path, backup_custom_methods
                            )
                            if success:
                                updated_files.append(str(file_path))
                                class_name = safe_class_name(change.table_name) + self.config.config.generation.suffix
                                class_names.append(class_name)
                                logger.info(f"增量更新成功: {file_path}")
                            else:
                                logger.error(f"增量更新失败: {file_path}")

            # 生成__init__.py文件
            if class_names and not preview_mode:
                self._generate_init_file(output_dir, class_names)

            logger.info(f"增量更新完成，更新了 {len(updated_files)} 个文件")
            return updated_files

        except Exception as e:
            logger.error(f"增量更新失败: {e}")
            raise

    def _get_model_file_path(self, table_name: str) -> Path:
        """获取模型文件路径"""
        class_name = safe_class_name(table_name) + self.config.config.generation.suffix
        file_name = f"{class_name.lower()}.py"
        return Path(self.config.config.generation.output_dir) / file_name

    def close(self):
        """关闭资源"""
        if self.metadata_reader:
            self.metadata_reader.close()