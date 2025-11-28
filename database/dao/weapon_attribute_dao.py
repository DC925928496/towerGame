"""
武器属性数据访问对象
处理武器属性的数据库操作
"""
from typing import List, Dict, Any, Optional
from database.dao.base_dao import BaseDAO
import logging

logger = logging.getLogger(__name__)


class WeaponAttributeDAO(BaseDAO):
    """武器属性数据访问对象"""

    def create(self, data: Dict[str, Any]) -> int:
        """创建武器属性记录"""
        query = """
        INSERT INTO weapon_attributes (
            player_id, attribute_type, value, level, description
        ) VALUES (
            %(player_id)s, %(attribute_type)s, %(value)s, %(level)s, %(description)s
        )
        """
        return self.execute_insert(query, data)

    def get_by_id(self, attribute_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取武器属性"""
        query = "SELECT * FROM weapon_attributes WHERE id = %s"
        result = self.execute_query(query, (attribute_id,))
        return result[0] if result else None

    def update(self, attribute_id: int, data: Dict[str, Any]) -> bool:
        """更新武器属性"""
        set_clauses = []
        params = []

        for key, value in data.items():
            if key != 'id':
                set_clauses.append(f"{key} = %s")
                params.append(value)

        if not set_clauses:
            return False

        params.append(attribute_id)
        query = f"UPDATE weapon_attributes SET {', '.join(set_clauses)} WHERE id = %s"
        return self.execute_update(query, params) > 0

    def delete(self, attribute_id: int) -> bool:
        """删除武器属性"""
        query = "DELETE FROM weapon_attributes WHERE id = %s"
        return self.execute_update(query, (attribute_id,)) > 0

    def get_by_player_id(self, player_id: int) -> List[Dict[str, Any]]:
        """根据玩家ID获取所有武器属性"""
        query = """
        SELECT * FROM weapon_attributes
        WHERE player_id = %s
        ORDER BY id ASC
        """
        return self.execute_query(query, (player_id,))

    def delete_by_player_id(self, player_id: int) -> int:
        """删除玩家的所有武器属性"""
        query = "DELETE FROM weapon_attributes WHERE player_id = %s"
        return self.execute_update(query, (player_id,))

    def create_player_attributes(self, player_id: int, attributes: List[Dict[str, Any]]) -> List[int]:
        """为玩家创建多个武器属性"""
        if not attributes:
            return []

        params_list = []
        for attr in attributes:
            params_list.append((
                player_id,
                attr.get('attribute_type'),
                attr.get('value'),
                attr.get('level', 0),
                attr.get('description', '')
            ))

        query = """
        INSERT INTO weapon_attributes (
            player_id, attribute_type, value, level, description
        ) VALUES (%s, %s, %s, %s, %s)
        """
        self.execute_batch(query, params_list)

        # 获取插入的ID列表（简化版本，返回最新属性数量）
        return list(range(len(attributes)))

    def update_player_attributes(self, player_id: int, attributes: List[Dict[str, Any]]) -> bool:
        """更新玩家的武器属性"""
        try:
            # 先删除现有属性
            self.delete_by_player_id(player_id)

            # 再创建新属性
            if attributes:
                self.create_player_attributes(player_id, attributes)

            return True
        except Exception as e:
            logger.error(f"更新玩家武器属性失败: {e}")
            return False

    def get_attribute_stats(self, player_id: int) -> Dict[str, Any]:
        """获取玩家武器属性统计"""
        query = """
        SELECT
            attribute_type,
            COUNT(*) as count,
            AVG(value) as avg_value,
            MAX(value) as max_value,
            MIN(value) as min_value
        FROM weapon_attributes
        WHERE player_id = %s
        GROUP BY attribute_type
        """
        results = self.execute_query(query, (player_id,))

        stats = {}
        for result in results:
            stats[result['attribute_type']] = {
                'count': result['count'],
                'avg_value': result['avg_value'],
                'max_value': result['max_value'],
                'min_value': result['min_value']
            }

        return stats