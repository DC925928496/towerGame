"""
玩家装备数据访问对象
处理玩家装备信息的数据库操作
"""
from typing import List, Dict, Any, Optional
from database.dao.base_dao import BaseDAO
from database.models import PlayerEquipmentModel
import logging

logger = logging.getLogger(__name__)


class EquipmentDAO(BaseDAO):
    """玩家装备数据访问对象"""

    def create(self, data: Dict[str, Any]) -> int:
        """创建装备记录"""
        query = """
        INSERT INTO player_equipment (
            player_id, equipment_type, item_name, attack_value,
            defense_value, rarity_level, is_equipped, slot_position,
            created_at, updated_at
        ) VALUES (
            %(player_id)s, %(equipment_type)s, %(item_name)s, %(attack_value)s,
            %(defense_value)s, %(rarity_level)s, %(is_equipped)s, %(slot_position)s,
            NOW(), NOW()
        )
        """
        return self.execute_insert(query, data)

    def get_by_id(self, equipment_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取装备"""
        query = "SELECT * FROM player_equipment WHERE id = %s"
        result = self.execute_query(query, (equipment_id,))
        return result[0] if result else None

    def update(self, equipment_id: int, data: Dict[str, Any]) -> bool:
        """更新装备信息"""
        set_clauses = []
        params = []

        for key, value in data.items():
            if key != 'id':
                set_clauses.append(f"{key} = %s")
                params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = NOW()")
        params.append(equipment_id)

        query = f"UPDATE player_equipment SET {', '.join(set_clauses)} WHERE id = %s"
        return self.execute_update(query, params) > 0

    def delete(self, equipment_id: int) -> bool:
        """删除装备记录"""
        query = "DELETE FROM player_equipment WHERE id = %s"
        return self.execute_update(query, (equipment_id,)) > 0

    def get_by_player_id(self, player_id: int) -> List[Dict[str, Any]]:
        """根据玩家ID获取所有装备"""
        query = """
        SELECT * FROM player_equipment
        WHERE player_id = %s
        ORDER BY is_equipped DESC, created_at ASC
        """
        return self.execute_query(query, (player_id,))

    def get_equipped_by_player(self, player_id: int, equipment_type: str) -> Optional[Dict[str, Any]]:
        """获取玩家当前装备的指定类型装备"""
        query = """
        SELECT * FROM player_equipment
        WHERE player_id = %s AND equipment_type = %s AND is_equipped = TRUE
        LIMIT 1
        """
        result = self.execute_query(query, (player_id, equipment_type))
        return result[0] if result else None

    def equip_item(self, player_id: int, equipment_id: int) -> bool:
        """装备物品"""
        try:
            # 先取消同类装备
            equipment = self.get_by_id(equipment_id)
            if not equipment:
                return False

            equipment_type = equipment['equipment_type']
            self.unequip_type(player_id, equipment_type)

            # 装备新物品
            data = {'is_equipped': True}
            return self.update(equipment_id, data)
        except Exception as e:
            logger.error(f"装备物品失败: {e}")
            return False

    def unequip_type(self, player_id: int, equipment_type: str) -> bool:
        """取消装备指定类型的物品"""
        query = """
        UPDATE player_equipment
        SET is_equipped = FALSE, updated_at = NOW()
        WHERE player_id = %s AND equipment_type = %s AND is_equipped = TRUE
        """
        return self.execute_update(query, (player_id, equipment_type)) > 0

    def unequip_item(self, equipment_id: int) -> bool:
        """取消装备指定物品"""
        data = {'is_equipped': False}
        return self.update(equipment_id, data)

    def save_equipment(self, player_id: int, equipment_type: str, item_name: str,
                     attack_value: int = 0, defense_value: int = 0,
                     rarity_level: str = 'common') -> int:
        """保存装备信息"""
        # 先取消同类装备
        self.unequip_type(player_id, equipment_type)

        # 创建新装备记录
        data = {
            'player_id': player_id,
            'equipment_type': equipment_type,
            'item_name': item_name,
            'attack_value': attack_value,
            'defense_value': defense_value,
            'rarity_level': rarity_level,
            'is_equipped': True,
            'slot_position': 1  # 默认位置
        }

        return self.create(data)

    def delete_by_player_id(self, player_id: int) -> int:
        """删除玩家的所有装备"""
        query = "DELETE FROM player_equipment WHERE player_id = %s"
        return self.execute_update(query, (player_id,))

    def get_equipment_stats(self, player_id: int) -> Dict[str, Any]:
        """获取玩家装备统计"""
        query = """
        SELECT
            equipment_type,
            COUNT(*) as count,
            SUM(CASE WHEN is_equipped THEN 1 ELSE 0 END) as equipped_count
        FROM player_equipment
        WHERE player_id = %s
        GROUP BY equipment_type
        """
        results = self.execute_query(query, (player_id,))

        stats = {}
        for result in results:
            stats[result['equipment_type']] = {
                'count': result['count'],
                'equipped_count': result['equipped_count']
            }

        return stats