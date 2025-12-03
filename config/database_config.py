"""
数据库配置管理类
处理MySQL数据库连接配置，从环境变量读取敏感信息
"""
import os
from typing import Optional
from dataclasses import dataclass
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class DatabaseConfig:
    """数据库配置类"""
    host: str
    port: int
    database: str
    user: str
    password: str
    charset: str = 'utf8mb4'

    # 连接池配置
    pool_size: int = 3  # 减少连接池大小，避免过多连接
    max_overflow: int = 5  # 减少最大溢出连接数
    pool_timeout: int = 60  # 增加获取连接的超时时间
    pool_recycle: int = 1800  # 减少连接回收时间到30分钟

    def get_connection_string(self) -> str:
        """获取数据库连接字符串"""
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"


class DatabaseConfigManager:
    """数据库配置管理器"""

    def __init__(self):
        self._config: Optional[DatabaseConfig] = None

    def load_config(self) -> DatabaseConfig:
        """从环境变量加载数据库配置"""
        if self._config is None:
            self._config = DatabaseConfig(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', '3306')),
                database=os.getenv('DB_NAME', 'tower_game'),
                user=os.getenv('DB_USER', ''),
                password=os.getenv('DB_PASSWORD', ''),
                pool_size=int(os.getenv('DB_POOL_SIZE', '3')),
                max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '5')),
                pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '60')),
                pool_recycle=int(os.getenv('DB_POOL_RECYCLE', '1800'))
            )
        return self._config

    def get_config(self) -> DatabaseConfig:
        """获取数据库配置（单例模式）"""
        return self.load_config()

    def is_configured(self) -> bool:
        """检查数据库是否已正确配置"""
        try:
            config = self.load_config()
            # 检查必要的配置项是否存在且不为空
            return (
                config.host and
                config.database and
                config.user and
                config.password and
                config.host.strip() != '' and
                config.database.strip() != '' and
                config.user.strip() != '' and
                config.password.strip() != ''
            )
        except Exception as e:
            return False


# 全局配置管理器实例
config_manager = DatabaseConfigManager()