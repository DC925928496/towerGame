"""
商人数据访问对象
处理商人信息的数据库操作
"""
from typing import List, Dict, Any, Optional
from database.dao.base_dao import BaseDAO
import logging

logger = logging.getLogger(__name__)


class MerchantDAO(BaseDAO):
    """商人数据访问对象"""

    def create(self, data: Dict[str, Any]) -> int:
        """创建商人记录"""
        query = """
        INSERT INTO floor_merchants (
            floor_id, merchant_name, merchant_type, is_active,
            created_at, updated_at
        ) VALUES (
            %(floor_id)s, %(merchant_name)s, %(merchant_type)s, %(is_active)s,
            NOW(), NOW()
        )
        """
        return self.execute_insert(query, data)

    def get_by_id(self, merchant_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取商人信息"""
        query = "SELECT * FROM floor_merchants WHERE id = %s"
        result = self.execute_query(query, (merchant_id,))
        return result[0] if result else None

    def update(self, merchant_id: int, data: Dict[str, Any]) -> bool:
        """更新商人信息"""
        set_clauses = []
        params = []

        for key, value in data.items():
            if key != 'id':
                set_clauses.append(f"{key} = %s")
                params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = NOW()")
        params.append(merchant_id)

        query = f"UPDATE floor_merchants SET {', '.join(set_clauses)} WHERE id = %s"
        return self.execute_update(query, params) > 0

    def delete(self, merchant_id: int) -> bool:
        """删除商人记录"""
        query = "DELETE FROM floor_merchants WHERE id = %s"
        return self.execute_update(query, (merchant_id,)) > 0

    def get_by_floor_id(self, floor_id: int) -> Optional[Dict[str, Any]]:
        """根据楼层ID获取商人信息"""
        query = """
        SELECT * FROM floor_merchants
        WHERE floor_id = %s AND is_active = TRUE
        LIMIT 1
        """
        result = self.execute_query(query, (floor_id,))
        return result[0] if result else None

    def save_merchant(self, floor_id: int, merchant_name: str,
                     merchant_type: str = 'general') -> int:
        """保存商人信息"""
        data = {
            'floor_id': floor_id,
            'merchant_name': merchant_name,
            'merchant_type': merchant_type,
            'is_active': True
        }

        return self.create(data)

    def delete_by_floor_id(self, floor_id: int) -> int:
        """删除楼层的商人"""
        query = "DELETE FROM floor_merchants WHERE floor_id = %s"
        return self.execute_update(query, (floor_id,))

    def get_merchant_stats(self, floor_id: Optional[int] = None) -> Dict[str, Any]:
        """获取商人统计信息"""
        if floor_id:
            query = """
            SELECT
                merchant_type,
                COUNT(*) as count,
                SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_count
            FROM floor_merchants
            WHERE floor_id = %s
            GROUP BY merchant_type
            """
            result = self.execute_query(query, (floor_id,))
        else:
            query = """
            SELECT
                merchant_type,
                COUNT(*) as count,
                SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_count
            FROM floor_merchants
            GROUP BY merchant_type
            """
            result = self.execute_query(query)

        stats = {}
        for item in result:
            stats[item['merchant_type']] = {
                'count': item['count'],
                'active_count': item['active_count']
            }

        return stats

    def get_all_merchants(self, is_active_only: bool = True) -> List[Dict[str, Any]]:
        """获取所有商人"""
        if is_active_only:
            query = """
            SELECT fm.*, sf.floor_level, sf.save_id
            FROM floor_merchants fm
            INNER JOIN saved_floors sf ON fm.floor_id = sf.id
            WHERE fm.is_active = TRUE
            ORDER BY sf.floor_level ASC
            """
        else:
            query = """
            SELECT fm.*, sf.floor_level, sf.save_id
            FROM floor_merchants fm
            INNER JOIN saved_floors sf ON fm.floor_id = sf.id
            ORDER BY sf.floor_level ASC
            """
        return self.execute_query(query)