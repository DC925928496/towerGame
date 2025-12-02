"""
简化的数据库连接池
用于解决连接问题
"""
import pymysql
import logging
from typing import Optional
from contextlib import contextmanager
from config.database_config import config_manager, DatabaseConfig

logger = logging.getLogger(__name__)


class SimpleDatabaseConnectionPool:
    """简化的数据库连接池"""

    def __init__(self):
        self._config: Optional[DatabaseConfig] = None
        self._initialize_pool()

    def _initialize_pool(self):
        """初始化连接池"""
        try:
            self._config = config_manager.get_config()
            logger.info(f"初始化简化数据库连接池，服务器: {self._config.host}:{self._config.port}")
        except Exception as e:
            logger.error(f"初始化连接池失败: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = None
        try:
            conn = self._create_connection()
            yield conn
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            if conn:
                try:
                    conn.close()
                    logger.debug("数据库连接已关闭")
                except:
                    pass

    def _create_connection(self) -> pymysql.Connection:
        """创建新的数据库连接"""
        try:
            connection = pymysql.Connect(
                host=self._config.host,
                port=self._config.port,
                user=self._config.user,
                password=self._config.password,
                database=self._config.database,
                charset=self._config.charset,
                autocommit=False,
                cursorclass=pymysql.cursors.DictCursor
            )
            logger.info("创建新的数据库连接成功")
            return connection
        except Exception as e:
            logger.error(f"创建数据库连接失败: {str(e)}")
            raise

    def test_connection(self) -> bool:
        """测试数据库连接是否可用"""
        try:
            conn = pymysql.Connect(
                host=self._config.host,
                port=self._config.port,
                user=self._config.user,
                password=self._config.password,
                database=self._config.database,
                charset=self._config.charset,
                autocommit=False,
                cursorclass=pymysql.cursors.DictCursor
            )
            conn.close()
            return True
        except Exception as e:
            logger.warning(f"数据库连接测试失败: {e}")
            return False

    def execute_query(self, query: str, params: tuple = None) -> list:
        """执行查询"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params or ())
                result = cursor.fetchall()
                logger.debug(f"查询成功，返回 {len(result)} 条记录")
                return result
            finally:
                cursor.close()

    def execute_update(self, query: str, params: tuple = None) -> int:
        """执行更新操作"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                affected_rows = cursor.execute(query, params or ())
                conn.commit()
                logger.debug(f"更新成功，影响 {affected_rows} 行")
                return affected_rows
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()

    def execute_insert(self, query: str, data: dict = None) -> int:
        """执行插入操作并返回ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if data:
                    cursor.execute(query, data)
                else:
                    cursor.execute(query)

                insert_id = cursor.lastrowid
                conn.commit()
                logger.debug(f"插入成功，ID: {insert_id}")
                return insert_id
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()

    def execute_batch(self, query: str, params_list: list) -> None:
        """批量执行操作"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(query, params_list)
                conn.commit()
                logger.debug(f"批量操作成功，执行 {len(params_list)} 条")
            except Exception:
                conn.rollback()
                raise
            finally:
                cursor.close()


# 全局连接池实例
connection_pool = SimpleDatabaseConnectionPool()
