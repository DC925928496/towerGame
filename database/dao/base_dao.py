"""
基础DAO类
提供数据库操作的通用接口和基础功能
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from database.simple_connection_pool import connection_pool
import logging

logger = logging.getLogger(__name__)


class BaseDAO(ABC):
    """数据访问对象基类"""

    def __init__(self):
        self.pool = connection_pool

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> int:
        """创建记录，返回新记录ID"""
        pass

    @abstractmethod
    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取记录"""
        pass

    @abstractmethod
    def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """更新记录，返回是否成功"""
        pass

    @abstractmethod
    def delete(self, record_id: int) -> bool:
        """删除记录，返回是否成功"""
        pass

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询语句"""
        return self.pool.execute_query(query, params)

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """执行更新/插入/删除语句，返回影响行数"""
        return self.pool.execute_update(query, params)

    def execute_insert(self, query: str, data: dict = None) -> int:
        """执行插入语句，返回新记录ID"""
        return self.pool.execute_insert(query, data)

    def execute_batch(self, query: str, params_list: List[tuple]) -> int:
        """批量执行语句，返回影响总行数"""
        self.pool.execute_batch(query, params_list)
        return len(params_list)

    def exists(self, table: str, condition: str, params: tuple = ()) -> bool:
        """检查记录是否存在"""
        query = f"SELECT COUNT(*) as count FROM {table} WHERE {condition}"
        result = self.execute_query(query, params)
        return result[0]['count'] > 0 if result else False

    def get_max_id(self, table: str, id_column: str = 'id') -> int:
        """获取表中最大ID"""
        query = f"SELECT MAX({id_column}) as max_id FROM {table}"
        result = self.execute_query(query)
        return result[0]['max_id'] or 0 if result else 0