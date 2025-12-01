"""数据库元数据读取器

负责从MySQL数据库读取表结构、字段信息、索引、外键等元数据
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Set
import logging
from contextlib import contextmanager
import pymysql.cursors
from pymysql import Error as MySQLError

from database.simple_connection_pool import SimpleDatabaseConnectionPool
from .config_manager import ConfigManager
from .utils import map_mysql_to_python_type, validate_table_name, format_comment

logger = logging.getLogger(__name__)

@dataclass
class ColumnMetadata:
    """列元数据"""
    name: str
    data_type: str
    python_type: str
    max_length: Optional[int] = None
    is_nullable: bool = True
    default_value: Optional[str] = None
    is_primary_key: bool = False
    is_auto_increment: bool = False
    is_unique: bool = False
    comment: str = ""
    ordinal_position: int = 0

    @property
    def has_default(self) -> bool:
        """是否有默认值"""
        return self.default_value is not None

    @property
    def is_required(self) -> bool:
        """是否为必填字段"""
        return not self.is_nullable and self.default_value is None

@dataclass
class IndexMetadata:
    """索引元数据"""
    name: str
    columns: List[str]
    is_unique: bool = False
    is_primary: bool = False
    index_type: str = "BTREE"

@dataclass
class ForeignKeyMetadata:
    """外键元数据"""
    name: str
    column: str
    referenced_table: str
    referenced_column: str
    on_delete: str = "RESTRICT"
    on_update: str = "RESTRICT"

    @property
    def property_name(self) -> str:
        """生成属性名"""
        # 移除_id后缀并转为驼峰命名
        if self.column.endswith('_id'):
            base_name = self.column[:-3]
            return base_name
        return self.column.replace('_', '')

    @property
    def referenced_class(self) -> str:
        """生成引用的类名"""
        from .utils import safe_class_name
        return safe_class_name(self.referenced_table) + "Model"

    def is_cascade_delete(self) -> bool:
        """是否级联删除"""
        return self.on_delete.upper() == "CASCADE"

    def is_cascade_update(self) -> bool:
        """是否级联更新"""
        return self.on_update.upper() == "CASCADE"

@dataclass
class TableMetadata:
    """表元数据"""
    name: str
    comment: str = ""
    engine: str = "InnoDB"
    charset: str = "utf8mb4"
    collation: str = "utf8mb4_unicode_ci"
    columns: List[ColumnMetadata] = None
    primary_keys: List[str] = None
    indexes: List[IndexMetadata] = None
    foreign_keys: List[ForeignKeyMetadata] = None
    row_count: int = 0

    def __post_init__(self):
        if self.columns is None:
            self.columns = []
        if self.primary_keys is None:
            self.primary_keys = []
        if self.indexes is None:
            self.indexes = []
        if self.foreign_keys is None:
            self.foreign_keys = []

    def get_column(self, name: str) -> Optional[ColumnMetadata]:
        """根据列名获取列元数据"""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def get_foreign_keys_for_column(self, column_name: str) -> List[ForeignKeyMetadata]:
        """获取指定列的外键信息"""
        return [fk for fk in self.foreign_keys if fk.column == column_name]

    def get_relationship_tables(self) -> Set[str]:
        """获取关联的表名集合"""
        related_tables = set()
        for fk in self.foreign_keys:
            related_tables.add(fk.referenced_table)
        return related_tables

    def get_foreign_key_columns(self) -> List[str]:
        """获取所有外键列名"""
        return [fk.column for fk in self.foreign_keys]

    def has_foreign_key_to(self, table_name: str) -> bool:
        """检查是否有到指定表的外键"""
        return any(fk.referenced_table == table_name for fk in self.foreign_keys)

    def get_foreign_key_to(self, table_name: str) -> Optional[ForeignKeyMetadata]:
        """获取到指定表的外键"""
        for fk in self.foreign_keys:
            if fk.referenced_table == table_name:
                return fk
        return None

    def get_validation_rules(self) -> Dict[str, List[str]]:
        """获取字段的验证规则"""
        rules = {}
        for col in self.columns:
            col_rules = []

            # 必填验证
            if col.is_required:
                col_rules.append("required")

            # 类型验证
            if col.python_type in ["int", "float"]:
                col_rules.append("numeric")
                if not col.is_nullable and col.python_type == "int" and col.name.endswith("_id"):
                    col_rules.append("positive_integer")
            elif col.python_type == "str":
                if col.max_length:
                    col_rules.append(f"max_length:{col.max_length}")
                if col.name.endswith("_email"):
                    col_rules.append("email")
                elif col.name.endswith("_url"):
                    col_rules.append("url")
                elif col.name.endswith("_phone"):
                    col_rules.append("phone")
            elif col.python_type == "datetime":
                col_rules.append("datetime")

            # 唯一性验证
            if col.is_unique:
                col_rules.append("unique")

            if col_rules:
                rules[col.name] = col_rules

        return rules

    def get_imports_needed(self) -> Set[str]:
        """获取需要的导入"""
        imports = set()
        for col in self.columns:
            if col.is_nullable and col.default_value is None:
                imports.add("Optional")
            if col.python_type == "datetime":
                imports.add("datetime")
            if col.python_type == "Decimal":
                imports.add("Decimal")

        if self.foreign_keys:
            imports.add("List")
            imports.add("Dict")
            imports.add("Any")

        return imports

class DatabaseMetadataReader:
    """数据库元数据读取器"""

    def __init__(self, config: ConfigManager):
        """
        初始化元数据读取器

        Args:
            config: 配置管理器
        """
        self.config = config
        self.connection_pool = None
        self._initialize_connection_pool()

    def _initialize_connection_pool(self):
        """初始化数据库连接池"""
        try:
            # 使用项目现有的连接池，它不接受参数，使用全局配置
            self.connection_pool = SimpleDatabaseConnectionPool()
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connection pool: {e}")
            raise

    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        return self.connection_pool.get_connection()

    def read_all_tables(self) -> List[TableMetadata]:
        """
        读取所有表的元数据

        Returns:
            表元数据列表
        """
        logger.info("Starting to read all table metadata")
        tables = []
        error_count = 0
        warning_count = 0

        try:
            with self.get_connection() as conn:
                # 获取所有表名
                table_names = self._get_table_names(conn)
                if not table_names:
                    logger.warning("No tables found in database")
                    return []

                logger.info(f"Found {len(table_names)} tables")

                # 读取每个表的详细信息
                for i, table_name in enumerate(table_names, 1):
                    if self.config.should_exclude_table(table_name):
                        logger.debug(f"Skipping excluded table: {table_name}")
                        continue

                    try:
                        table_metadata = self.read_table_metadata(table_name)
                        if table_metadata:
                            # 验证表元数据的完整性
                            validation_errors = self._validate_table_metadata(table_metadata)
                            if validation_errors:
                                warning_count += len(validation_errors)
                                logger.warning(f"Validation warnings for table {table_name}: {validation_errors}")
                                # 仍然继续处理，但记录警告

                            tables.append(table_metadata)
                            logger.debug(f"Successfully read metadata for table: {table_name} ({i}/{len(table_names)})")
                        else:
                            logger.warning(f"No metadata returned for table: {table_name}")
                            warning_count += 1
                    except MySQLError as e:
                        error_count += 1
                        logger.error(f"Database error reading metadata for table {table_name}: {e}")
                        continue
                    except Exception as e:
                        error_count += 1
                        logger.error(f"Unexpected error reading metadata for table {table_name}: {e}")
                        continue

                logger.info(f"Successfully read metadata for {len(tables)} tables with {error_count} errors and {warning_count} warnings")

                # 如果错误太多，发出警告
                if error_count > 0:
                    error_rate = error_count / len(table_names)
                    if error_rate > 0.5:
                        logger.warning(f"High error rate ({error_rate:.1%}) detected when reading table metadata")

                return tables

        except MySQLError as e:
            logger.error(f"Database connection error while reading all tables: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error while reading all tables: {e}")
            raise

    def read_table_metadata(self, table_name: str) -> Optional[TableMetadata]:
        """
        读取单个表的元数据

        Args:
            table_name: 表名

        Returns:
            表元数据对象，如果读取失败返回None
        """
        if not validate_table_name(table_name):
            logger.warning(f"Invalid table name: {table_name}")
            return None

        try:
            with self.get_connection() as conn:
                # 读取表基本信息
                table_info = self._read_table_info(conn, table_name)
                if not table_info:
                    logger.warning(f"Table {table_name} not found")
                    return None

                # 读取列信息
                columns = self._read_columns(conn, table_name)
                if not columns:
                    logger.error(f"No columns found for table {table_name}")
                    return None

                # 读取索引信息
                try:
                    indexes = self._read_indexes(conn, table_name)
                except Exception as e:
                    logger.warning(f"Failed to read indexes for table {table_name}: {e}")
                    indexes = []

                # 读取外键信息
                try:
                    foreign_keys = self._read_foreign_keys(conn, table_name)
                except Exception as e:
                    logger.warning(f"Failed to read foreign keys for table {table_name}: {e}")
                    foreign_keys = []

                # 提取主键
                primary_keys = [col.name for col in columns if col.is_primary_key]

                # 创建表元数据对象
                table_metadata = TableMetadata(
                    name=table_name,
                    comment=table_info.get('comment', ''),
                    engine=table_info.get('engine', 'InnoDB'),
                    charset=table_info.get('charset', 'utf8mb4'),
                    collation=table_info.get('collation', 'utf8mb4_unicode_ci'),
                    columns=columns,
                    primary_keys=primary_keys,
                    indexes=indexes,
                    foreign_keys=foreign_keys,
                    row_count=table_info.get('row_count', 0)
                )

                logger.debug(f"Successfully read metadata for table {table_name}")
                return table_metadata

        except MySQLError as e:
            logger.error(f"Database error reading metadata for table {table_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error reading metadata for table {table_name}: {e}")
            return None

    def _validate_table_metadata(self, table: TableMetadata) -> List[str]:
        """
        验证表元数据的完整性

        Args:
            table: 表元数据

        Returns:
            验证错误列表
        """
        errors = []

        # 检查是否有列
        if not table.columns:
            errors.append("Table has no columns")

        # 检查是否有主键（除了某些特殊情况）
        if not table.primary_keys and table.name not in ['log_table', 'temp_table']:
            errors.append("Table has no primary key")

        # 检查列名的有效性
        for col in table.columns:
            if not col.name or col.name.strip() == '':
                errors.append("Found empty column name")

            # 检查是否使用保留字
            if col.name.lower() in ['order', 'group', 'where', 'select', 'from']:
                errors.append(f"Column '{col.name}' uses reserved SQL word")

            # 检查Python类型的有效性
            if not col.python_type:
                errors.append(f"Column '{col.name}' has invalid Python type")

        # 检查外键的有效性
        for fk in table.foreign_keys:
            # 检查外键列是否存在
            if not any(col.name == fk.column for col in table.columns):
                errors.append(f"Foreign key column '{fk.column}' does not exist in table")

            # 检查引用表名的有效性
            if not fk.referenced_table or fk.referenced_table.strip() == '':
                errors.append(f"Invalid referenced table name for foreign key '{fk.name}'")

        return errors

    def _get_table_names(self, conn) -> List[str]:
        """获取所有表名"""
        query = """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """

        try:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return [row['TABLE_NAME'] for row in cursor.fetchall()]
        except MySQLError as e:
            logger.error(f"Failed to get table names: {e}")
            raise

    def _read_table_info(self, conn, table_name: str) -> Optional[Dict[str, Any]]:
        """读取表的基本信息"""
        query = """
        SELECT
            TABLE_COMMENT as comment,
            ENGINE as engine,
            TABLE_COLLATION as collation,
            TABLE_ROWS as row_count
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        """

        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (table_name,))
                result = cursor.fetchone()
                return dict(result) if result else None
        except MySQLError as e:
            logger.error(f"Failed to read table info for {table_name}: {e}")
            return None

    def _read_columns(self, conn, table_name: str) -> List[ColumnMetadata]:
        """读取表的列信息"""
        query = """
        SELECT
            COLUMN_NAME,
            COLUMN_TYPE,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            COLUMN_COMMENT,
            ORDINAL_POSITION,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """

        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (table_name,))
                rows = cursor.fetchall()

                columns = []
                for row in rows:
                    # 确定是否可为空
                    is_nullable = row['IS_NULLABLE'] == 'YES'

                    # 映射到Python类型
                    python_type = map_mysql_to_python_type(
                        row['COLUMN_TYPE'],
                        is_nullable,
                        row['COLUMN_DEFAULT']
                    )

                    column = ColumnMetadata(
                        name=row['COLUMN_NAME'],
                        data_type=row['COLUMN_TYPE'],
                        python_type=python_type,
                        max_length=row['CHARACTER_MAXIMUM_LENGTH'],
                        is_nullable=is_nullable,
                        default_value=row['COLUMN_DEFAULT'],
                        comment=format_comment(row['COLUMN_COMMENT']),
                        ordinal_position=row['ORDINAL_POSITION']
                    )

                    columns.append(column)

                # 获取主键和自增信息
                self._enrich_columns_with_constraints(conn, table_name, columns)

                return columns

        except MySQLError as e:
            logger.error(f"Failed to read columns for table {table_name}: {e}")
            raise

    def _enrich_columns_with_constraints(self, conn, table_name: str, columns: List[ColumnMetadata]):
        """丰富列的约束信息（主键、自增、唯一索引等）"""
        # 获取主键信息
        primary_key_query = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND CONSTRAINT_NAME = 'PRIMARY'
        ORDER BY ORDINAL_POSITION
        """

        # 获取自增信息
        auto_increment_query = f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND EXTRA = 'auto_increment'
        """

        try:
            with conn.cursor() as cursor:
                # 获取主键
                cursor.execute(primary_key_query, (table_name,))
                primary_keys = [row['COLUMN_NAME'] for row in cursor.fetchall()]

                # 获取自增列
                cursor.execute(auto_increment_query, (table_name,))
                auto_increment_columns = [row['COLUMN_NAME'] for row in cursor.fetchall()]

                # 更新列信息
                for column in columns:
                    column.is_primary_key = column.name in primary_keys
                    column.is_auto_increment = column.name in auto_increment_columns

        except MySQLError as e:
            logger.warning(f"Failed to enrich column constraints for table {table_name}: {e}")

    def _read_indexes(self, conn, table_name: str) -> List[IndexMetadata]:
        """读取表的索引信息"""
        query = """
        SELECT
            INDEX_NAME,
            COLUMN_NAME,
            NON_UNIQUE,
            INDEX_TYPE
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """

        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (table_name,))
                rows = cursor.fetchall()

                # 按索引名分组
                index_data = {}
                for row in rows:
                    index_name = row['INDEX_NAME']
                    if index_name not in index_data:
                        index_data[index_name] = {
                            'columns': [],
                            'is_unique': row['NON_UNIQUE'] == 0,
                            'is_primary': index_name == 'PRIMARY',
                            'index_type': row['INDEX_TYPE']
                        }
                    index_data[index_name]['columns'].append(row['COLUMN_NAME'])

                # 创建索引元数据对象
                indexes = []
                for index_name, data in index_data.items():
                    index = IndexMetadata(
                        name=index_name,
                        columns=data['columns'],
                        is_unique=data['is_unique'],
                        is_primary=data['is_primary'],
                        index_type=data['index_type']
                    )
                    indexes.append(index)

                return indexes

        except MySQLError as e:
            logger.error(f"Failed to read indexes for table {table_name}: {e}")
            return []

    def _read_foreign_keys(self, conn, table_name: str) -> List[ForeignKeyMetadata]:
        """读取表的外键信息"""
        query = """
        SELECT
            kcu.CONSTRAINT_NAME,
            kcu.COLUMN_NAME,
            rc.REFERENCED_TABLE_NAME,
            kcu.REFERENCED_COLUMN_NAME,
            rc.DELETE_RULE,
            rc.UPDATE_RULE
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu
        JOIN INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS rc
            ON kcu.CONSTRAINT_NAME = rc.CONSTRAINT_NAME
            AND kcu.CONSTRAINT_SCHEMA = rc.CONSTRAINT_SCHEMA
        WHERE kcu.TABLE_SCHEMA = DATABASE()
            AND kcu.TABLE_NAME = %s
            AND rc.REFERENCED_TABLE_NAME IS NOT NULL
        """

        try:
            with conn.cursor() as cursor:
                cursor.execute(query, (table_name,))
                rows = cursor.fetchall()

                foreign_keys = []
                for row in rows:
                    fk = ForeignKeyMetadata(
                        name=row['CONSTRAINT_NAME'],
                        column=row['COLUMN_NAME'],
                        referenced_table=row['REFERENCED_TABLE_NAME'],
                        referenced_column=row['REFERENCED_COLUMN_NAME'],
                        on_delete=row['DELETE_RULE'],
                        on_update=row['UPDATE_RULE']
                    )
                    foreign_keys.append(fk)

                return foreign_keys

        except MySQLError as e:
            logger.error(f"Failed to read foreign keys for table {table_name}: {e}")
            return []

    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def close(self):
        """关闭连接池"""
        # 现有的简单连接池没有close_all方法
        logger.info("Database connection pool cleanup completed")