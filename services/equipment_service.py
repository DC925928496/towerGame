"""
装备服务层
处理装备相关的业务逻辑
"""
from services.base_service import BaseService
from database.dao.equipment_dao import EquipmentDAO
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class EquipmentService(BaseService):
    """装备服务层"""

    def __init__(self):
        super().__init__()
        self.equipment_dao = self.dao_manager.equipment

    def create_equipment(self, player_id: int, equipment_type: str, item_name: str,
                        attack_value: int = 0, defense_value: int = 0,
                        rarity_level: str = 'common') -> int:
        """创建新装备"""
        self.validate_id(player_id, "玩家ID")
        self.validate_string(item_name, "装备名称")
        self.validate_string(equipment_type, "装备类型")

        try:
            self.log_operation(f"创建装备: {item_name} (玩家ID: {player_id})")
            return self.equipment_dao.create({
                'player_id': player_id,
                'equipment_type': equipment_type,
                'item_name': item_name,
                'attack_value': attack_value,
                'defense_value': defense_value,
                'rarity_level': rarity_level,
                'is_equipped': False,
                'slot_position': 1
            })
        except Exception as e:
            self.handle_error(e, "创建装备")

    def get_player_equipment(self, player_id: int) -> List[Dict[str, Any]]:
        """获取玩家的所有装备"""
        self.validate_id(player_id, "玩家ID")

        try:
            return self.equipment_dao.get_by_player_id(player_id)
        except Exception as e:
            self.handle_error(e, "获取玩家装备")

    def get_equipped_equipment(self, player_id: int, equipment_type: str = None) -> List[Dict[str, Any]]:
        """获取玩家已装备的装备"""
        self.validate_id(player_id, "玩家ID")

        try:
            if equipment_type:
                equipment = self.equipment_dao.get_equipped_by_player(player_id, equipment_type)
                return [equipment] if equipment else []
            else:
                return self.equipment_dao.get_by_player_id(player_id)
        except Exception as e:
            self.handle_error(e, "获取已装备装备")

    def equip_item(self, player_id: int, equipment_id: int) -> bool:
        """装备物品"""
        self.validate_id(player_id, "玩家ID")
        self.validate_id(equipment_id, "装备ID")

        try:
            self.log_operation(f"装备物品: 玩家{player_id}, 装备ID{equipment_id}")
            return self.equipment_dao.equip_item(player_id, equipment_id)
        except Exception as e:
            self.handle_error(e, "装备物品")

    def unequip_item(self, player_id: int, equipment_type: str) -> bool:
        """卸下指定类型的装备"""
        self.validate_id(player_id, "玩家ID")
        self.validate_string(equipment_type, "装备类型")

        try:
            self.log_operation(f"卸下装备: 玩家{player_id}, 类型{equipment_type}")
            return self.equipment_dao.unequip_type(player_id, equipment_type)
        except Exception as e:
            self.handle_error(e, "卸下装备")

    def save_equipment(self, player_id: int, equipment_type: str, item_name: str,
                     attack_value: int = 0, defense_value: int = 0,
                     rarity_level: str = 'common') -> int:
        """保存装备信息（会自动替换同类型装备）"""
        self.validate_id(player_id, "玩家ID")
        self.validate_string(item_name, "装备名称")
        self.validate_string(equipment_type, "装备类型")

        try:
            self.log_operation(f"保存装备: {item_name} (玩家ID: {player_id})")
            return self.equipment_dao.save_equipment(
                player_id, equipment_type, item_name,
                attack_value, defense_value, rarity_level
            )
        except Exception as e:
            self.handle_error(e, "保存装备")

    def delete_equipment(self, equipment_id: int) -> bool:
        """删除装备"""
        self.validate_id(equipment_id, "装备ID")

        try:
            self.log_operation(f"删除装备: ID{equipment_id}")
            return self.equipment_dao.delete(equipment_id) > 0
        except Exception as e:
            self.handle_error(e, "删除装备")

    def get_equipment_by_id(self, equipment_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取装备"""
        self.validate_id(equipment_id, "装备ID")

        try:
            return self.equipment_dao.get_by_id(equipment_id)
        except Exception as e:
            self.handle_error(e, "获取装备")

    def update_equipment(self, equipment_id: int, data: Dict[str, Any]) -> bool:
        """更新装备信息"""
        self.validate_id(equipment_id, "装备ID")

        if not isinstance(data, dict) or not data:
            raise ValueError("更新数据必须是非空字典")

        try:
            self.log_operation(f"更新装备: ID{equipment_id}")
            return self.equipment_dao.update(equipment_id, data)
        except Exception as e:
            self.handle_error(e, "更新装备")

    def delete_player_equipment(self, player_id: int) -> bool:
        """删除玩家的所有装备"""
        self.validate_id(player_id, "玩家ID")

        try:
            self.log_operation(f"删除玩家所有装备: 玩家{player_id}")
            return self.equipment_dao.delete_by_player_id(player_id) > 0
        except Exception as e:
            self.handle_error(e, "删除玩家装备")

    def get_equipment_stats(self, player_id: int) -> Dict[str, Any]:
        """获取玩家装备统计"""
        self.validate_id(player_id, "玩家ID")

        try:
            return self.equipment_dao.get_equipment_stats(player_id)
        except Exception as e:
            self.handle_error(e, "获取装备统计")