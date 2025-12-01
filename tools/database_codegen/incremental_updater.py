"""增量更新管理器

负责检测表结构变化，智能更新实体类，保护用户自定义代码
"""

import re
import os
import difflib
import pickle
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum

from .metadata_reader import TableMetadata, ColumnMetadata
from .utils import safe_class_name

logger = logging.getLogger(__name__)

class ChangeType(Enum):
    """变更类型枚举"""
    TABLE_ADDED = "table_added"
    TABLE_REMOVED = "table_removed"
    TABLE_MODIFIED = "table_modified"
    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"
    COLUMN_MODIFIED = "column_modified"
    INDEX_ADDED = "index_added"
    INDEX_REMOVED = "index_removed"
    INDEX_MODIFIED = "index_modified"

class TableChange:
    """表变更信息"""
    def __init__(self, change_type: ChangeType, table_name: str,
                 details: Dict = None, old_metadata: TableMetadata = None,
                 new_metadata: TableMetadata = None):
        self.change_type = change_type
        self.table_name = table_name
        self.details = details or {}
        self.old_metadata = old_metadata
        self.new_metadata = new_metadata

class IncrementalUpdater:
    """增量更新管理器"""

    USER_CUSTOM_METHODS_START = "# === USER_CUSTOM_METHODS_START ==="
    USER_CUSTOM_METHODS_END = "# === USER_CUSTOM_METHODS_END ==="

    def __init__(self, config_manager):
        self.config = config_manager
        self.metadata_cache_dir = Path("database/models/.metadata_cache")
        self.metadata_cache_dir.mkdir(exist_ok=True)

    def detect_changes(self, current_metadata: List[TableMetadata],
                        backup_custom_methods: bool = True) -> List[TableChange]:
        """
        检测表结构变化

        Args:
            current_metadata: 当前数据库表元数据
            backup_custom_methods: 是否备份用户自定义方法

        Returns:
            检测到的变更列表
        """
        logger.info("开始检测数据库表结构变化")

        # 加载缓存的元数据
        cached_metadata = self._load_cached_metadata()

        # 转换为字典便于比较
        current_tables = {table.name: table for table in current_metadata}
        cached_tables = {table.name: table for table in cached_metadata}

        current_table_names = set(current_tables.keys())
        cached_table_names = set(cached_tables.keys())

        changes = []

        # 检测新增的表
        added_tables = current_table_names - cached_table_names
        for table_name in added_tables:
            changes.append(TableChange(
                ChangeType.TABLE_ADDED,
                table_name,
                new_metadata=current_tables[table_name]
            ))
            logger.info(f"检测到新增表: {table_name}")

        # 检测删除的表
        removed_tables = cached_table_names - current_table_names
        for table_name in removed_tables:
            changes.append(TableChange(
                ChangeType.TABLE_REMOVED,
                table_name,
                old_metadata=cached_tables[table_name]
            ))
            logger.info(f"检测到删除表: {table_name}")

        # 检测修改的表
        common_tables = current_table_names & cached_table_names
        for table_name in common_tables:
            table_changes = self._detect_table_changes(
                cached_tables[table_name],
                current_tables[table_name],
                backup_custom_methods
            )

            if table_changes:
                changes.extend([
                    TableChange(
                        ChangeType.TABLE_MODIFIED,
                        table_name,
                        details=change_details,
                        old_metadata=cached_tables[table_name],
                        new_metadata=current_tables[table_name]
                    )
                    for change_details in table_changes
                ])
                logger.info(f"检测到表 {table_name} 的 {len(table_changes)} 个变更")

        # 保存当前元数据到缓存
        self._save_cached_metadata(current_metadata)

        logger.info(f"变化检测完成，共发现 {len(changes)} 个变更")
        return changes

    def _detect_table_changes(self, old_table: TableMetadata,
                           new_table: TableMetadata,
                           backup_custom_methods: bool) -> List[Dict]:
        """
        检测单个表的变化

        Args:
            old_table: 旧的表元数据
            new_table: 新的表元数据
            backup_custom_methods: 是否备份用户自定义方法

        Returns:
            变更详情列表
        """
        changes = []

        # 检测字段变化
        old_columns = {col.name: col for col in old_table.columns}
        new_columns = {col.name: col for col in new_table.columns}

        old_column_names = set(old_columns.keys())
        new_column_names = set(new_columns.keys())

        # 新增字段
        added_columns = new_column_names - old_column_names
        for col_name in added_columns:
            col = new_columns[col_name]
            changes.append({
                'type': ChangeType.COLUMN_ADDED,
                'column_name': col_name,
                'column_type': col.python_type,
                'nullable': col.is_nullable,
                'default': col.default_value,
                'comment': col.comment
            })

        # 删除字段
        removed_columns = old_column_names - new_column_names
        for col_name in removed_columns:
            col = old_columns[col_name]
            changes.append({
                'type': ChangeType.COLUMN_REMOVED,
                'column_name': col_name,
                'column_type': col.python_type,
                'comment': col.comment
            })

        # 修改字段
        common_columns = old_column_names & new_column_names
        for col_name in common_columns:
            old_col = old_columns[col_name]
            new_col = new_columns[col_name]

            if old_col != new_col:
                change_details = {
                    'type': ChangeType.COLUMN_MODIFIED,
                    'column_name': col_name,
                    'old_type': old_col.python_type,
                    'new_type': new_col.python_type,
                    'old_nullable': old_col.is_nullable,
                    'new_nullable': new_col.is_nullable,
                    'old_default': old_col.default_value,
                    'new_default': new_col.default_value,
                    'old_comment': old_col.comment,
                    'new_comment': new_col.comment
                }

                # 检查具体哪些属性发生了变化
                changed_attrs = []
                if old_col.python_type != new_col.python_type:
                    changed_attrs.append('type')
                if old_col.is_nullable != new_col.is_nullable:
                    changed_attrs.append('nullable')
                if old_col.default_value != new_col.default_value:
                    changed_attrs.append('default')
                if old_col.comment != new_col.comment:
                    changed_attrs.append('comment')

                if changed_attrs:
                    change_details['changed_attrs'] = changed_attrs
                    changes.append(change_details)

        # 检测索引变化
        old_indexes = {idx.name: idx for idx in old_table.indexes}
        new_indexes = {idx.name: idx for idx in new_table.indexes}

        old_index_names = set(old_indexes.keys())
        new_index_names = set(new_indexes.keys())

        # 新增索引
        added_indexes = new_index_names - old_index_names
        for idx_name in added_indexes:
            idx = new_indexes[idx_name]
            changes.append({
                'type': ChangeType.INDEX_ADDED,
                'index_name': idx_name,
                'columns': idx.columns,
                'is_unique': idx.is_unique
            })

        # 删除索引
        removed_indexes = old_index_names - new_index_names
        for idx_name in removed_indexes:
            idx = old_indexes[idx_name]
            changes.append({
                'type': ChangeType.INDEX_REMOVED,
                'index_name': idx_name,
                'columns': idx.columns,
                'is_unique': idx.is_unique
            })

        # 修改索引
        common_indexes = old_index_names & new_index_names
        for idx_name in common_indexes:
            old_idx = old_indexes[idx_name]
            new_idx = new_indexes[idx_name]

            if old_idx != new_idx:
                changes.append({
                    'type': ChangeType.INDEX_MODIFIED,
                    'index_name': idx_name,
                    'old_columns': old_idx.columns,
                    'new_columns': new_idx.columns,
                    'old_unique': old_idx.is_unique,
                    'new_unique': new_idx.is_unique
                })

        return changes

    def backup_user_methods(self, file_path: Path) -> Optional[str]:
        """
        备份用户自定义方法

        Args:
            file_path: 文件路径

        Returns:
            用户自定义方法内容，如果没有则返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            start_index = content.find(self.USER_CUSTOM_METHODS_START)
            end_index = content.find(self.USER_CUSTOM_METHODS_END)

            if start_index != -1 and end_index != -1:
                # 提取用户自定义方法区域（包含标记）
                user_methods = content[start_index:end_index + len(self.USER_CUSTOM_METHODS_END)]

                # 保存到备份文件
                backup_path = file_path.with_suffix('.custom_methods.bak')
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(user_methods)

                logger.info(f"备份用户自定义方法到: {backup_path}")
                return user_methods

        except Exception as e:
            logger.warning(f"备份用户自定义方法失败 {file_path}: {e}")

        return None

    def restore_user_methods(self, file_path: Path, generated_content: str) -> str:
        """
        恢复用户自定义方法到生成的内容中

        Args:
            file_path: 文件路径
            generated_content: 新生成的文件内容

        Returns:
            合并后的内容
        """
        try:
            # 查找备份文件
            backup_path = file_path.with_suffix('.custom_methods.bak')

            if not backup_path.exists():
                return generated_content

            with open(backup_path, 'r', encoding='utf-8') as f:
                user_methods = f.read()

            # 查找生成内容中的自定义方法区域
            start_marker_pos = generated_content.find(self.USER_CUSTOM_METHODS_START)
            end_marker_pos = generated_content.find(self.USER_CUSTOM_METHODS_END)

            if start_marker_pos != -1 and end_marker_pos != -1:
                # 替换自定义方法区域
                before_marker = generated_content[:start_marker_pos]
                after_marker = generated_content[end_marker_pos + len(self.USER_CUSTOM_METHODS_END):]

                merged_content = before_marker + user_methods + after_marker
                logger.info(f"恢复用户自定义方法到: {file_path}")
                return merged_content
            else:
                # 如果找不到标记区域，在文件末尾添加
                return generated_content.rstrip() + "\n\n" + user_methods + "\n"

        except Exception as e:
            logger.warning(f"恢复用户自定义方法失败 {file_path}: {e}")

        return generated_content

    def apply_incremental_update(self, table_metadata: TableMetadata,
                                file_path: Path,
                                backup_custom_methods: bool = True) -> bool:
        """
        应用增量更新到指定文件

        Args:
            table_metadata: 表元数据
            file_path: 文件路径
            backup_custom_methods: 是否备份用户自定义方法

        Returns:
            更新是否成功
        """
        try:
            # 备份用户自定义方法
            user_methods = None
            if backup_custom_methods and file_path.exists():
                user_methods = self.backup_user_methods(file_path)

            # 重新生成文件
            from .entity_generator import EntityGenerator
            from .template_engine import TemplateEngine

            template_engine = TemplateEngine(self.config)
            generated_content = template_engine.render_entity_template(table_metadata)

            # 恢复用户自定义方法
            if user_methods:
                generated_content = self.restore_user_methods(file_path, generated_content)

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(generated_content)

            logger.info(f"增量更新完成: {file_path}")
            return True

        except Exception as e:
            logger.error(f"增量更新失败 {file_path}: {e}")
            return False

    def _load_cached_metadata(self) -> List[TableMetadata]:
        """加载缓存的元数据"""
        cached_metadata = []

        for cache_file in self.metadata_cache_dir.glob("*.metadata"):
            try:
                import pickle
                with open(cache_file, 'rb') as f:
                    table_meta = pickle.load(f)
                    cached_metadata.append(table_meta)
            except Exception as e:
                logger.warning(f"加载缓存元数据失败 {cache_file}: {e}")

        return cached_metadata

    def _save_cached_metadata(self, metadata: List[TableMetadata]):
        """保存元数据到缓存"""
        for table in metadata:
            try:
                import pickle
                cache_file = self.metadata_cache_dir / f"{table.name}.metadata"
                with open(cache_file, 'wb') as f:
                    pickle.dump(table, f)
            except Exception as e:
                logger.warning(f"保存缓存元数据失败 {table.name}: {e}")

    def clear_cache(self):
        """清除缓存"""
        try:
            import shutil
            if self.metadata_cache_dir.exists():
                shutil.rmtree(self.metadata_cache_dir)
                self.metadata_cache_dir.mkdir(exist_ok=True)
                logger.info("清除元数据缓存完成")
        except Exception as e:
            logger.error(f"清除缓存失败: {e}")