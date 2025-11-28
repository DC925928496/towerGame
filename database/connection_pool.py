"""
MySQL数据库连接池实现
提供连接池管理、自动重连和错误恢复功能
"""
import pymysql
import logging
from typing import Optional
from contextlib import contextmanager
from config.database_config import config_manager, DatabaseConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """MySQL数据库连接池"""

    def __init__(self):
        self._pool = []
        self._active_connections = 0
        self._config: Optional[DatabaseConfig] = None
        self._initialize_pool()

    def _initialize_pool(self):
        """初始化连接池"""
        try:
            self._config = config_manager.get_config()
            logger.info(f"初始化数据库连接池，服务器: {self._config.host}:{self._config.port}")
        except Exception as e:
            logger.error(f"初始化连接池失败: {e}")
            raise

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

    def _get_connection(self) -> pymysql.Connection:
        """从连接池获取连接"""
        # 如果连接池为空，创建新连接
        if not self._pool and self._active_connections < self._config.pool_size:
            try:
                conn = self._create_connection()
                self._active_connections += 1
                logger.debug(f"从连接池获取连接，当前活跃连接数: {self._active_connections}")
                return conn
            except Exception as e:
                logger.error(f"获取数据库连接失败: {e}")
                raise

        # 尝试从连接池获取连接
        if self._pool:
            conn = self._pool.pop()
            if self._is_connection_valid(conn):
                self._active_connections += 1
                logger.debug(f"从连接池复用连接，当前活跃连接数: {self._active_connections}")
                return conn
            else:
                # 连接无效，关闭并创建新连接
                try:
                    conn.close()
                except:
                    pass
                return self._get_connection()

        # 如果超过连接池大小，检查溢出
        if self._active_connections >= self._config.pool_size + self._config.max_overflow:
            raise Exception("连接池已满，无法获取新连接")

        # 创建临时连接（溢出）
        try:
            conn = self._create_connection()
            self._active_connections += 1
            logger.debug(f"创建溢出连接，当前活跃连接数: {self._active_connections}")
            return conn
        except Exception as e:
            logger.error(f"获取溢出连接失败: {e}")
            raise


    def _is_connection_valid(self, conn: pymysql.Connection) -> bool:
        """检查连接是否有效"""
        try:
            conn.ping(reconnect=False)
            return True
        except:
            return False

    def _return_connection(self, conn: pymysql.Connection):
        """归还连接到连接池"""
        try:
            if self._is_connection_valid(conn):
                # 重置连接状态
                conn.rollback()
                self._pool.append(conn)
                logger.debug("连接归还到连接池")
            else:
                # 连接无效，直接关闭
                try:
                    conn.close()
                except:
                    pass
                logger.debug("无效连接已关闭")
        except Exception as e:
            logger.error(f"归还连接时出错: {e}")
        finally:
            self._active_connections = max(0, self._active_connections - 1)
            logger.debug(f"当前活跃连接数: {self._active_connections}")

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = None
        try:
            conn = self._get_connection()
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
                self._return_connection(conn)

    @contextmanager
    def get_cursor(self):
        """获取数据库游标的上下文管理器"""
        with self.get_connection() as conn:
            cursor = None
            try:
                cursor = conn.cursor()
                yield cursor
                conn.commit()
            except Exception as e:
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                logger.error(f"数据库操作失败: {e}")
                raise
            finally:
                if cursor:
                    cursor.close()

    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.get_connection() as conn:
                conn.ping()
                logger.info("数据库连接测试成功")
                return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False

    def close_all(self):
        """关闭所有连接"""
        try:
            # 关闭连接池中的所有连接
            while self._pool:
                conn = self._pool.pop()
                try:
                    conn.close()
                except:
                    pass

            logger.info("所有数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭连接时出错: {e}")


# 全局连接池实例
connection_pool = DatabaseConnectionPool()