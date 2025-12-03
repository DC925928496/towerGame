"""
装备属性数据访问对象
处理武器和防具属性的数据库操作
支持通过equipment_type字段区分武器和防具
"""
from typing import List, Dict, Any, Optional
from database.dao.base_dao import BaseDAO
import logging

logger = logging.getLogger(__name__)


class EquipmentAttributeDAO(BaseDAO):
    """装备属性数据访问对象"""

    def create(self, data: Dict[str, Any]) -> int:
        """创建装备属性记录"""
        query = """
        INSERT INTO weapon_attributes (
            player_id, attribute_type, value, level, description
        ) VALUES (
            %(player_id)s, %(attribute_type)s, %(value)s, %(level)s, %(description)s
        )
        """
        return self.execute_insert(query, data)

    def create_for_equipment(self, data: Dict[str, Any]) -> int:
        """创建装备属性记录（包含equipment_type字段）"""
        # 检查是否需要添加equipment_type字段
        # 如果数据库表还没有这个字段，我们先创建记录
        if 'equipment_type' in data:
            # 如果表已经支持equipment_type字段，使用这个查询
            try:
                query = """
                INSERT INTO weapon_attributes (
                    player_id, attribute_type, value, level, description, equipment_type
                ) VALUES (
                    %(player_id)s, %(attribute_type)s, %(value)s, %(level)s, %(description)s, %(equipment_type)s
                )
                """
                return self.execute_insert(query, data)
            except Exception as e:
                # 如果字段不存在，回退到不包含equipment_type的查询
                logger.warning(f"equipment_type字段不存在，使用兼容模式: {e}")

        # 兼容模式：不包含equipment_type
        query = """
        INSERT INTO weapon_attributes (
            player_id, attribute_type, value, level, description
        ) VALUES (
            %(player_id)s, %(attribute_type)s, %(value)s, %(level)s, %(description)s
        )
        """
        return self.execute_insert(query, data)

    def get_by_id(self, attribute_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取装备属性"""
        query = "SELECT * FROM weapon_attributes WHERE id = %s"
        result = self.execute_query(query, (attribute_id,))
        return result[0] if result else None

    def get_by_player(self, player_id: int, equipment_type: str = None) -> List[Dict[str, Any]]:
        """根据玩家ID获取装备属性列表"""
        if equipment_type:
            # 如果支持equipment_type字段
            try:
                query = """
                SELECT * FROM weapon_attributes
                WHERE player_id = %s AND equipment_type = %s
                ORDER BY id
                """
                result = self.execute_query(query, (player_id, equipment_type))
                if result:
                    return result
            except Exception as e:
                # 如果字段不存在，获取所有属性并按attribute_type过滤
                logger.warning(f"equipment_type字段不存在，使用属性类型过滤: {e}")

        # 兼容模式：根据attribute_type推断equipment_type
        query = "SELECT * FROM weapon_attributes WHERE player_id = %s ORDER BY id"
        result = self.execute_query(query, (player_id,))

        if equipment_type:
            # 根据attribute_type判断是武器还是防具
            from game_model import ATTRIBUTE_TYPES, ARMOR_ATTRIBUTE_TYPES
            weapon_types = set(ATTRIBUTE_TYPES.keys())
            armor_types = set(ARMOR_ATTRIBUTE_TYPES.keys())

            filtered_result = []
            for attr in result:
                if equipment_type == 'weapon' and attr['attribute_type'] in weapon_types:
                    filtered_result.append(attr)
                elif equipment_type == 'armor' and attr['attribute_type'] in armor_types:
                    filtered_result.append(attr)

            return filtered_result

        return result

    def update(self, attribute_id: int, data: Dict[str, Any]) -> bool:
        """更新装备属性"""
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
        """删除装备属性"""
        query = "DELETE FROM weapon_attributes WHERE id = %s"
        return self.execute_update(query, (attribute_id,)) > 0

    def delete_by_player(self, player_id: int, equipment_type: str = None) -> bool:
        """删除玩家的所有装备属性"""
        if equipment_type:
            # 使用get_by_player的逻辑来过滤
            attributes = self.get_by_player(player_id, equipment_type)
            deleted_count = 0
            for attr in attributes:
                if self.delete(attr['id']):
                    deleted_count += 1
            return deleted_count > 0
        else:
            query = "DELETE FROM weapon_attributes WHERE player_id = %s"
            return self.execute_update(query, (player_id,)) > 0

    def get_player_weapon_attributes(self, player_id: int) -> List[Dict[str, Any]]:
        """获取玩家武器属性"""
        return self.get_by_player(player_id, 'weapon')

    def get_player_armor_attributes(self, player_id: int) -> List[Dict[str, Any]]:
        """获取玩家防具属性"""
        return self.get_by_player(player_id, 'armor')

    def create_armor_attributes(self, player_id: int, armor_attributes: List) -> List[int]:
        """批量创建防具属性"""
        created_ids = []
        for attr in armor_attributes:
            data = {
                'player_id': player_id,
                'attribute_type': attr.attribute_type,
                'value': attr.value,
                'level': attr.level,
                'description': attr.description,
                'equipment_type': 'armor'
            }
            attr_id = self.create_for_equipment(data)
            if attr_id > 0:
                created_ids.append(attr_id)
        return created_ids

    def create_weapon_attributes(self, player_id: int, weapon_attributes: List) -> List[int]:
        """批量创建武器属性"""
        created_ids = []
        for attr in weapon_attributes:
            data = {
                'player_id': player_id,
                'attribute_type': attr.attribute_type,
                'value': attr.value,
                'level': attr.level,
                'description': attr.description,
                'equipment_type': 'weapon'
            }
            attr_id = self.create_for_equipment(data)
            if attr_id > 0:
                created_ids.append(attr_id)
        return created_ids

    def clear_player_equipment_attributes(self, player_id: int, equipment_type: str = None) -> bool:
        """清除玩家的装备属性"""
        return self.delete_by_player(player_id, equipment_type)

    def get_by_player_and_type(self, player_id: int, equipment_type: str) -> List[Dict[str, Any]]:
        """根据玩家ID和装备类型获取属性列表（别名方法）"""
        return self.get_by_player(player_id, equipment_type)

    def delete_by_player_and_type(self, player_id: int, equipment_type: str) -> bool:
        """根据玩家ID和装备类型删除属性（别名方法）"""
        return self.delete_by_player(player_id, equipment_type)

    def create_player_attributes(self, player_id: int, attributes_data: List[Dict[str, Any]]) -> bool:
        """批量创建玩家装备属性"""
        success_count = 0
        for attr_data in attributes_data:
            if self.create_for_equipment(attr_data) > 0:
                success_count += 1
        return success_count > 0