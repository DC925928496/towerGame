"""
商人服务层
处理商人相关的业务逻辑
"""
from services.base_service import BaseService
from database.dao.merchant_dao import MerchantDAO
from database.dao.merchant_inventory_dao import MerchantInventoryDAO
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class MerchantService(BaseService):
    """商人服务层"""

    def __init__(self):
        super().__init__()
        self.merchant_dao = self.dao_manager.merchant
        self.merchant_inventory_dao = self.dao_manager.merchant_inventory

    def create_merchant(self, floor_id: int, merchant_name: str, merchant_type: str = 'general') -> int:
        """创建商人"""
        self.validate_id(floor_id, "楼层ID")
        self.validate_string(merchant_name, "商人名")
        self.validate_string(merchant_type, "商人类型")

        try:
            merchant_id = self.merchant_dao.save_merchant(floor_id, merchant_name, merchant_type)
            self.log_operation(f"创建商人: {merchant_name} 类型:{merchant_type}")
            return merchant_id
        except Exception as e:
            self.handle_error(e, "创建商人")

    def get_merchant(self, merchant_id: int) -> Optional[Dict[str, Any]]:
        """获取商人信息"""
        self.validate_id(merchant_id, "商人ID")

        try:
            return self.merchant_dao.get_by_id(merchant_id)
        except Exception as e:
            self.handle_error(e, "获取商人信息")

    def get_floor_merchant(self, floor_id: int) -> Optional[Dict[str, Any]]:
        """获取楼层商人"""
        self.validate_id(floor_id, "楼层ID")

        try:
            merchant = self.merchant_dao.get_by_floor_id(floor_id)
            if merchant:
                # 获取商人库存
                merchant['inventory'] = self.merchant_inventory_dao.get_by_merchant_id(merchant['id'])
            return merchant
        except Exception as e:
            self.handle_error(e, "获取楼层商人")

    def get_merchant_inventory(self, merchant_id: int) -> List[Dict[str, Any]]:
        """获取商人库存"""
        self.validate_id(merchant_id, "商人ID")

        try:
            return self.merchant_inventory_dao.get_by_merchant_id(merchant_id)
        except Exception as e:
            self.handle_error(e, "获取商人库存")

    def get_floor_merchant_inventory(self, floor_id: int) -> List[Dict[str, Any]]:
        """获取楼层商人库存"""
        self.validate_id(floor_id, "楼层ID")

        try:
            return self.merchant_inventory_dao.get_by_floor_id(floor_id)
        except Exception as e:
            self.handle_error(e, "获取楼层商人库存")

    def add_inventory_item(self, merchant_id: int, item_data: Dict[str, Any]) -> int:
        """添加库存物品"""
        self.validate_id(merchant_id, "商人ID")

        # 验证物品数据
        self.validate_string(item_data.get('name', ''), "物品名")
        self.validate_non_negative(item_data.get('quantity', 1), "数量")
        self.validate_non_negative(item_data.get('price', 10), "价格")

        try:
            inventory_data = {
                'merchant_id': merchant_id,
                'item_name': item_data['name'],
                'item_type': item_data.get('type', 'item'),
                'quantity': item_data.get('quantity', 1),
                'price': item_data.get('price', 10),
                'rarity_level': item_data.get('rarity', 'common'),
                'effect_type': item_data.get('effect_type', ''),
                'effect_value': item_data.get('effect_value', 0)
            }

            item_id = self.merchant_inventory_dao.create(inventory_data)
            self.log_operation(f"添加库存物品: {inventory_data['item_name']} x{inventory_data['quantity']}")
            return item_id
        except Exception as e:
            self.handle_error(e, "添加库存物品")

    def update_inventory_quantity(self, inventory_id: int, quantity: int) -> bool:
        """更新库存数量"""
        self.validate_id(inventory_id, "库存ID")
        self.validate_non_negative(quantity, "数量")

        try:
            success = self.merchant_inventory_dao.update_quantity(inventory_id, quantity)
            if success:
                self.log_operation(f"更新库存数量: 库存{inventory_id} -> {quantity}")
            return success
        except Exception as e:
            self.handle_error(e, "更新库存数量")

    def sell_item(self, inventory_id: int, amount: int = 1) -> bool:
        """出售物品（减少库存）"""
        self.validate_id(inventory_id, "库存ID")
        self.validate_non_negative(amount, "出售数量")

        if amount <= 0:
            return False

        try:
            inventory_item = self.merchant_inventory_dao.get_by_id(inventory_id)
            if not inventory_item:
                raise ValueError("库存物品不存在")

            if inventory_item['quantity'] < amount:
                raise ValueError("库存不足")

            success = self.merchant_inventory_dao.decrease_quantity(inventory_id, amount)
            if success:
                self.log_operation(f"出售物品: {inventory_item['item_name']} x{amount}")
            return success
        except Exception as e:
            self.handle_error(e, "出售物品")

    def buy_item(self, inventory_id: int, amount: int = 1) -> bool:
        """收购物品（增加库存）"""
        self.validate_id(inventory_id, "库存ID")
        self.validate_non_negative(amount, "收购数量")

        if amount <= 0:
            return False

        try:
            inventory_item = self.merchant_inventory_dao.get_by_id(inventory_id)
            if not inventory_item:
                raise ValueError("库存物品不存在")

            success = self.merchant_inventory_dao.increase_quantity(inventory_id, amount)
            if success:
                self.log_operation(f"收购物品: {inventory_item['item_name']} x{amount}")
            return success
        except Exception as e:
            self.handle_error(e, "收购物品")

    def get_items_by_type(self, merchant_id: int, item_type: str) -> List[Dict[str, Any]]:
        """获取指定类型的库存物品"""
        self.validate_id(merchant_id, "商人ID")
        self.validate_string(item_type, "物品类型")

        try:
            return self.merchant_inventory_dao.get_by_item_type(merchant_id, item_type)
        except Exception as e:
            self.handle_error(e, "获取指定类型库存")

    def get_items_by_rarity(self, merchant_id: int, rarity_level: str) -> List[Dict[str, Any]]:
        """获取指定稀有度的库存物品"""
        self.validate_id(merchant_id, "商人ID")
        self.validate_string(rarity_level, "稀有度")

        try:
            return self.merchant_inventory_dao.get_by_rarity(merchant_id, rarity_level)
        except Exception as e:
            self.handle_error(e, "获取指定稀有度库存")

    def get_merchant_shop_items(self, floor_id: int) -> List[Dict[str, Any]]:
        """获取商人商店的物品（用于交易界面）"""
        self.validate_id(floor_id, "楼层ID")

        try:
            items = self.merchant_inventory_dao.get_merchant_all_items(floor_id)
            self.log_operation(f"获取楼层{floor_id}商人商店物品，共{len(items)}件")
            return items
        except Exception as e:
            self.handle_error(e, "获取商人商店物品")

    def save_merchant_inventory(self, merchant_id: int, items: List[Dict[str, Any]]) -> List[int]:
        """保存商人整个库存"""
        self.validate_id(merchant_id, "商人ID")

        if not items:
            return []

        try:
            item_ids = self.merchant_inventory_dao.save_merchant_inventory(merchant_id, items)
            self.log_operation(f"保存商人库存: 商人{merchant_id}，共{len(items)}种物品")
            return item_ids
        except Exception as e:
            self.handle_error(e, "保存商人库存")

    def delete_merchant(self, merchant_id: int) -> bool:
        """删除商人"""
        self.validate_id(merchant_id, "商人ID")

        try:
            merchant = self.get_merchant(merchant_id)
            if not merchant:
                raise ValueError("商人不存在")

            # 先删除库存
            self.merchant_inventory_dao.delete_by_merchant_id(merchant_id)

            # 再删除商人
            success = self.merchant_dao.delete(merchant_id)
            if success:
                self.log_operation(f"删除商人: {merchant['merchant_name']}")
            return success
        except Exception as e:
            self.handle_error(e, "删除商人")

    def delete_floor_merchant(self, floor_id: int) -> int:
        """删除楼层商人"""
        self.validate_id(floor_id, "楼层ID")

        try:
            # 先删除商人库存
            merchant = self.merchant_dao.get_by_floor_id(floor_id)
            if merchant:
                self.merchant_inventory_dao.delete_by_merchant_id(merchant['id'])

            # 再删除商人
            count = self.merchant_dao.delete_by_floor_id(floor_id)
            if count > 0:
                self.log_operation(f"删除楼层{floor_id}的商人")
            return count
        except Exception as e:
            self.handle_error(e, "删除楼层商人")

    def get_merchant_stats(self, floor_id: int = None) -> Dict[str, Any]:
        """获取商人统计信息"""
        if floor_id:
            self.validate_id(floor_id, "楼层ID")

        try:
            merchant_stats = self.merchant_dao.get_merchant_stats(floor_id)

            if floor_id:
                # 获取库存统计
                merchant = self.merchant_dao.get_by_floor_id(floor_id)
                if merchant:
                    inventory_stats = self.merchant_inventory_dao.get_inventory_stats(merchant['id'])
                    merchant_stats['inventory'] = inventory_stats

            return merchant_stats
        except Exception as e:
            self.handle_error(e, "获取商人统计信息")