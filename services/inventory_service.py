"""
背包道具服务层
处理玩家道具管理的业务逻辑
"""
from services.base_service import BaseService
from database.dao.inventory_dao import InventoryDAO
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class InventoryService(BaseService):
    """背包道具服务层"""

    def __init__(self):
        super().__init__()
        self.inventory_dao = self.dao_manager.inventory

    def add_item(self, player_id: int, item_name: str, quantity: int = 1) -> bool:
        """添加道具到背包"""
        self.validate_id(player_id, "玩家ID")
        self.validate_string(item_name, "道具名称")
        self.validate_positive(quantity, "道具数量")

        try:
            self.log_operation(f"添加道具: {item_name} x{quantity} (玩家ID: {player_id})")
            result = self.inventory_dao.add_item(player_id, item_name, quantity)
            return result > 0
        except Exception as e:
            self.handle_error(e, "添加道具")

    def get_player_inventory(self, player_id: int) -> List[Dict[str, Any]]:
        """获取玩家的所有道具"""
        self.validate_id(player_id, "玩家ID")

        try:
            return self.inventory_dao.get_player_inventory(player_id)
        except Exception as e:
            self.handle_error(e, "获取玩家背包")

    def get_item(self, player_id: int, item_name: str) -> Optional[Dict[str, Any]]:
        """获取玩家指定的道具"""
        self.validate_id(player_id, "玩家ID")
        self.validate_string(item_name, "道具名称")

        try:
            return self.inventory_dao.get_item(player_id, item_name)
        except Exception as e:
            self.handle_error(e, "获取道具")

    def consume_item(self, player_id: int, item_name: str, quantity: int = 1) -> bool:
        """消耗道具"""
        self.validate_id(player_id, "玩家ID")
        self.validate_string(item_name, "道具名称")
        self.validate_positive(quantity, "消耗数量")

        try:
            self.log_operation(f"消耗道具: {item_name} x{quantity} (玩家ID: {player_id})")
            return self.inventory_dao.consume_item(player_id, item_name, quantity)
        except Exception as e:
            self.handle_error(e, "消耗道具")

    def update_item_quantity(self, player_id: int, item_name: str, quantity: int) -> bool:
        """更新道具数量"""
        self.validate_id(player_id, "玩家ID")
        self.validate_string(item_name, "道具名称")
        self.validate_non_negative(quantity, "道具数量")

        try:
            self.log_operation(f"更新道具数量: {item_name} -> {quantity} (玩家ID: {player_id})")
            return self.inventory_dao.update_item_quantity(player_id, item_name, quantity)
        except Exception as e:
            self.handle_error(e, "更新道具数量")

    def transfer_item(self, from_player_id: int, to_player_id: int, item_name: str, quantity: int) -> bool:
        """转移道具"""
        self.validate_id(from_player_id, "源玩家ID")
        self.validate_id(to_player_id, "目标玩家ID")
        self.validate_string(item_name, "道具名称")
        self.validate_positive(quantity, "转移数量")

        try:
            self.log_operation(f"转移道具: {item_name} x{quantity} (从{from_player_id}到{to_player_id})")
            return self.inventory_dao.transfer_item(from_player_id, to_player_id, item_name, quantity)
        except Exception as e:
            self.handle_error(e, "转移道具")

    def clear_inventory(self, player_id: int) -> bool:
        """清空玩家背包"""
        self.validate_id(player_id, "玩家ID")

        try:
            self.log_operation(f"清空背包: 玩家{player_id}")
            return self.inventory_dao.clear_inventory(player_id)
        except Exception as e:
            self.handle_error(e, "清空背包")

    def get_inventory_summary(self, player_id: int) -> Dict[str, int]:
        """获取背包统计摘要"""
        self.validate_id(player_id, "玩家ID")

        try:
            return self.inventory_dao.get_inventory_summary(player_id)
        except Exception as e:
            self.handle_error(e, "获取背包统计")

    def get_items_by_type(self, player_id: int, item_type: str) -> List[Dict[str, Any]]:
        """根据道具类型获取道具"""
        self.validate_id(player_id, "玩家ID")
        self.validate_string(item_type, "道具类型")

        try:
            return self.inventory_dao.get_items_by_type(player_id, item_type)
        except Exception as e:
            self.handle_error(e, "获取类型道具")

    def has_item(self, player_id: int, item_name: str, quantity: int = 1) -> bool:
        """检查玩家是否有足够的道具"""
        self.validate_id(player_id, "玩家ID")
        self.validate_string(item_name, "道具名称")
        self.validate_positive(quantity, "检查数量")

        try:
            item = self.get_item(player_id, item_name)
            return item and item['quantity'] >= quantity
        except Exception as e:
            self.handle_error(e, "检查道具")

    def get_item_quantity(self, player_id: int, item_name: str) -> int:
        """获取道具数量"""
        self.validate_id(player_id, "玩家ID")
        self.validate_string(item_name, "道具名称")

        try:
            item = self.get_item(player_id, item_name)
            return item['quantity'] if item else 0
        except Exception as e:
            self.handle_error(e, "获取道具数量")