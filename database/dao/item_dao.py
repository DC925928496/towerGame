"""
物品数据访问对象
处理物品和道具的数据库操作
"""
from typing import List, Dict, Any, Optional
from database.dao.base_dao import BaseDAO
import logging

logger = logging.getLogger(__name__)


class ItemDAO(BaseDAO):
    """物品数据访问对象"""

    def create(self, data: Dict[str, Any]) -> int:
        """创建物品记录"""
        query = """
        INSERT INTO floor_items (
            floor_id, item_type, item_name, symbol, effect_type,
            effect_value, position_x, position_y, rarity_level,
            created_at, updated_at
        ) VALUES (
            %(floor_id)s, %(item_type)s, %(item_name)s, %(symbol)s,
            %(effect_type)s, %(effect_value)s, %(position_x)s, %(position_y)s,
            %(rarity_level)s, NOW(), NOW()
        )
        """
        return self.execute_insert(query, data)

    def get_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取物品"""
        query = "SELECT * FROM floor_items WHERE id = %s"
        result = self.execute_query(query, (item_id,))
        return result[0] if result else None

    def update(self, item_id: int, data: Dict[str, Any]) -> bool:
        """更新物品信息"""
        set_clauses = []
        params = []

        for key, value in data.items():
            if key != 'id':
                set_clauses.append(f"{key} = %s")
                params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = NOW()")
        params.append(item_id)

        query = f"UPDATE floor_items SET {', '.join(set_clauses)} WHERE id = %s"
        return self.execute_update(query, params) > 0

    def delete(self, item_id: int) -> bool:
        """删除物品记录"""
        query = "DELETE FROM floor_items WHERE id = %s"
        return self.execute_update(query, (item_id,)) > 0

    def get_by_floor_id(self, floor_id: int) -> List[Dict[str, Any]]:
        """根据楼层ID获取所有物品"""
        query = """
        SELECT * FROM floor_items
        WHERE floor_id = %s
        ORDER BY position_y, position_x ASC
        """
        return self.execute_query(query, (floor_id,))

    def save_floor_items(self, floor_id: int, items: List[Dict[str, Any]]) -> List[int]:
        """保存楼层物品"""
        if not items:
            return []

        params_list = []
        for item in items:
            params_list.append((
                floor_id,
                item.get('item_type', 'item'),
                item.get('name', ''),
                item.get('symbol', '+'),
                item.get('effect_type', ''),
                item.get('effect_value', 0),
                item.get('position', {}).get('x', 0),
                item.get('position', {}).get('y', 0),
                item.get('rarity', 'common')
            ))

        query = """
        INSERT INTO floor_items (
            floor_id, item_type, item_name, symbol, effect_type,
            effect_value, position_x, position_y, rarity_level
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.execute_batch(query, params_list)

        # 返回插入的ID数量（简化版本）
        return list(range(len(items)))

    def delete_by_floor_id(self, floor_id: int) -> int:
        """删除楼层的所有物品"""
        query = "DELETE FROM floor_items WHERE floor_id = %s"
        return self.execute_update(query, (floor_id,))

    def get_items_by_position(self, floor_id: int, x: int, y: int) -> List[Dict[str, Any]]:
        """获取指定位置的物品"""
        query = """
        SELECT * FROM floor_items
        WHERE floor_id = %s AND position_x = %s AND position_y = %s
        """
        return self.execute_query(query, (floor_id, x, y))

    def update_item_position(self, item_id: int, x: int, y: int) -> bool:
        """更新物品位置"""
        data = {
            'position_x': x,
            'position_y': y
        }
        return self.update(item_id, data)

    def get_item_stats(self, floor_id: int) -> Dict[str, Any]:
        """获取楼层物品统计"""
        query = """
        SELECT
            item_type,
            effect_type,
            COUNT(*) as count,
            AVG(effect_value) as avg_value
        FROM floor_items
        WHERE floor_id = %s
        GROUP BY item_type, effect_type
        """
        results = self.execute_query(query, (floor_id,))

        stats = {}
        for result in results:
            key = f"{result['item_type']}_{result['effect_type']}"
            stats[key] = {
                'count': result['count'],
                'avg_value': result['avg_value']
            }

        return stats