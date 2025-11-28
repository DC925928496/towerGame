"""
楼层数据访问对象
处理楼层信息的数据库操作
"""
from typing import List, Dict, Any, Optional
from database.dao.base_dao import BaseDAO
import logging

logger = logging.getLogger(__name__)


class FloorDAO(BaseDAO):
    """楼层数据访问对象"""

    def create(self, data: Dict[str, Any]) -> int:
        """创建楼层记录"""
        query = """
        INSERT INTO saved_floors (
            save_id, floor_level, width, height, player_start_x,
            player_start_y, stairs_x, stairs_y, is_merchant_floor,
            created_at, updated_at
        ) VALUES (
            %(save_id)s, %(floor_level)s, %(width)s, %(height)s,
            %(player_start_x)s, %(player_start_y)s, %(stairs_x)s, %(stairs_y)s,
            %(is_merchant_floor)s, NOW(), NOW()
        )
        """
        return self.execute_insert(query, data)

    def get_by_id(self, floor_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取楼层信息"""
        query = "SELECT * FROM saved_floors WHERE id = %s"
        result = self.execute_query(query, (floor_id,))
        return result[0] if result else None

    def update(self, floor_id: int, data: Dict[str, Any]) -> bool:
        """更新楼层信息"""
        set_clauses = []
        params = []

        for key, value in data.items():
            if key != 'id':
                set_clauses.append(f"{key} = %s")
                params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = NOW()")
        params.append(floor_id)

        query = f"UPDATE saved_floors SET {', '.join(set_clauses)} WHERE id = %s"
        return self.execute_update(query, params) > 0

    def delete(self, floor_id: int) -> bool:
        """删除楼层记录"""
        query = "DELETE FROM saved_floors WHERE id = %s"
        return self.execute_update(query, (floor_id,)) > 0

    def get_by_save_id(self, save_id: int) -> Optional[Dict[str, Any]]:
        """根据存档ID获取楼层信息"""
        query = """
        SELECT * FROM saved_floors
        WHERE save_id = %s
        ORDER BY floor_level DESC
        LIMIT 1
        """
        result = self.execute_query(query, (save_id,))
        return result[0] if result else None

    def get_by_save_and_level(self, save_id: int, floor_level: int) -> Optional[Dict[str, Any]]:
        """根据存档ID和楼层级别获取楼层信息"""
        query = """
        SELECT * FROM saved_floors
        WHERE save_id = %s AND floor_level = %s
        """
        result = self.execute_query(query, (save_id, floor_level))
        return result[0] if result else None

    def save_floor_data(self, save_id: int, floor_level: int, floor_data: Dict[str, Any]) -> int:
        """保存楼层数据"""
        data = {
            'save_id': save_id,
            'floor_level': floor_level,
            'width': floor_data.get('width', 15),
            'height': floor_data.get('height', 15),
            'player_start_x': floor_data.get('player_start_pos', {}).get('x', 7),
            'player_start_y': floor_data.get('player_start_pos', {}).get('y', 7),
            'stairs_x': floor_data.get('stairs_pos', {}).get('x', 0),
            'stairs_y': floor_data.get('stairs_pos', {}).get('y', 0),
            'is_merchant_floor': floor_data.get('is_merchant_floor', False)
        }

        return self.create(data)

    def get_floors_by_save(self, save_id: int) -> List[Dict[str, Any]]:
        """获取存档的所有楼层"""
        query = """
        SELECT * FROM saved_floors
        WHERE save_id = %s
        ORDER BY floor_level ASC
        """
        return self.execute_query(query, (save_id,))

    def delete_by_save_id(self, save_id: int) -> int:
        """删除存档的所有楼层"""
        query = "DELETE FROM saved_floors WHERE save_id = %s"
        return self.execute_update(query, (save_id,))

    def get_floor_stats(self, save_id: int) -> Dict[str, Any]:
        """获取楼层统计信息"""
        query = """
        SELECT
            COUNT(*) as total_floors,
            MAX(floor_level) as max_floor,
            MIN(floor_level) as min_floor,
            SUM(CASE WHEN is_merchant_floor THEN 1 ELSE 0 END) as merchant_floors
        FROM saved_floors
        WHERE save_id = %s
        """
        result = self.execute_query(query, (save_id,))
        return result[0] if result else {}

    def get_max_floor_level(self, save_id: int) -> int:
        """获取存档的最大楼层"""
        query = "SELECT MAX(floor_level) as max_level FROM saved_floors WHERE save_id = %s"
        result = self.execute_query(query, (save_id,))
        return result[0]['max_level'] or 0 if result else 0