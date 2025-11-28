"""
商家库存数据访问对象
处理商家库存物品的数据库操作
"""
from typing import List, Dict, Any, Optional
from database.dao.base_dao import BaseDAO
import logging

logger = logging.getLogger(__name__)


class MerchantInventoryDAO(BaseDAO):
    """商家库存数据访问对象"""

    def create(self, data: Dict[str, Any]) -> int:
        """创建库存记录"""
        query = """
        INSERT INTO merchant_inventories (
            merchant_id, item_name, item_type, quantity, price,
            rarity_level, effect_type, effect_value, created_at, updated_at
        ) VALUES (
            %(merchant_id)s, %(item_name)s, %(item_type)s, %(quantity)s,
            %(price)s, %(rarity_level)s, %(effect_type)s, %(effect_value)s,
            NOW(), NOW()
        )
        """
        return self.execute_insert(query, data)

    def get_by_id(self, inventory_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取库存物品"""
        query = """
        SELECT mi.*, fm.merchant_name
        FROM merchant_inventories mi
        LEFT JOIN floor_merchants fm ON mi.merchant_id = fm.id
        WHERE mi.id = %s
        """
        result = self.execute_query(query, (inventory_id,))
        return result[0] if result else None

    def update(self, inventory_id: int, data: Dict[str, Any]) -> bool:
        """更新库存信息"""
        set_clauses = []
        params = []

        for key, value in data.items():
            if key != 'id':
                set_clauses.append(f"{key} = %s")
                params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = NOW()")
        params.append(inventory_id)

        query = f"UPDATE merchant_inventories SET {', '.join(set_clauses)} WHERE id = %s"
        return self.execute_update(query, params) > 0

    def delete(self, inventory_id: int) -> bool:
        """删除库存记录"""
        query = "DELETE FROM merchant_inventories WHERE id = %s"
        return self.execute_update(query, (inventory_id,)) > 0

    def get_by_merchant_id(self, merchant_id: int) -> List[Dict[str, Any]]:
        """获取商家的所有库存物品"""
        query = """
        SELECT * FROM merchant_inventories
        WHERE merchant_id = %s
        ORDER BY item_type, item_name ASC
        """
        return self.execute_query(query, (merchant_id,))

    def get_by_floor_id(self, floor_id: int) -> List[Dict[str, Any]]:
        """通过楼层ID获取商人库存"""
        query = """
        SELECT mi.* FROM merchant_inventories mi
        INNER JOIN floor_merchants fm ON mi.merchant_id = fm.id
        WHERE fm.floor_id = %s AND fm.is_active = TRUE
        ORDER BY mi.item_type, mi.item_name
        """
        return self.execute_query(query, (floor_id,))

    def save_merchant_inventory(self, merchant_id: int, items: List[Dict[str, Any]]) -> List[int]:
        """保存商人库存"""
        if not items:
            return []

        # 先删除旧库存
        self.delete_by_merchant_id(merchant_id)

        params_list = []
        for item in items:
            params_list.append((
                merchant_id,
                item.get('name', ''),
                item.get('type', 'item'),
                item.get('quantity', 1),
                item.get('price', 10),
                item.get('rarity', 'common'),
                item.get('effect_type', ''),
                item.get('effect_value', 0)
            ))

        query = """
        INSERT INTO merchant_inventories (
            merchant_id, item_name, item_type, quantity, price,
            rarity_level, effect_type, effect_value
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.execute_batch(query, params_list)

        # 返回插入的ID数量（简化版本）
        return list(range(len(items)))

    def delete_by_merchant_id(self, merchant_id: int) -> int:
        """删除商家的所有库存"""
        query = "DELETE FROM merchant_inventories WHERE merchant_id = %s"
        return self.execute_update(query, (merchant_id,))

    def update_quantity(self, inventory_id: int, quantity: int) -> bool:
        """更新库存数量"""
        if quantity < 0:
            return False

        data = {'quantity': quantity}
        return self.update(inventory_id, data)

    def decrease_quantity(self, inventory_id: int, amount: int = 1) -> bool:
        """减少库存数量"""
        query = """
        UPDATE merchant_inventories
        SET quantity = GREATEST(0, quantity - %s), updated_at = NOW()
        WHERE id = %s AND quantity >= %s
        """
        return self.execute_update(query, (amount, inventory_id, amount)) > 0

    def increase_quantity(self, inventory_id: int, amount: int = 1) -> bool:
        """增加库存数量"""
        query = """
        UPDATE merchant_inventories
        SET quantity = quantity + %s, updated_at = NOW()
        WHERE id = %s
        """
        return self.execute_update(query, (amount, inventory_id)) > 0

    def get_by_item_type(self, merchant_id: int, item_type: str) -> List[Dict[str, Any]]:
        """获取商人指定类型的库存物品"""
        query = """
        SELECT * FROM merchant_inventories
        WHERE merchant_id = %s AND item_type = %s AND quantity > 0
        ORDER BY price ASC
        """
        return self.execute_query(query, (merchant_id, item_type))

    def get_by_rarity(self, merchant_id: int, rarity_level: str) -> List[Dict[str, Any]]:
        """获取商人指定稀有度的库存物品"""
        query = """
        SELECT * FROM merchant_inventories
        WHERE merchant_id = %s AND rarity_level = %s AND quantity > 0
        ORDER BY price ASC
        """
        return self.execute_query(query, (merchant_id, rarity_level))

    def get_available_items(self, merchant_id: int) -> List[Dict[str, Any]]:
        """获取商家的可售物品（数量大于0）"""
        query = """
        SELECT * FROM merchant_inventories
        WHERE merchant_id = %s AND quantity > 0
        ORDER BY item_type, price ASC
        """
        return self.execute_query(query, (merchant_id,))

    def get_inventory_stats(self, merchant_id: int) -> Dict[str, Any]:
        """获取库存统计信息"""
        query = """
        SELECT
            item_type,
            COUNT(*) as item_count,
            SUM(quantity) as total_quantity,
            AVG(price) as avg_price,
            MIN(price) as min_price,
            MAX(price) as max_price
        FROM merchant_inventories
        WHERE merchant_id = %s
        GROUP BY item_type
        """
        results = self.execute_query(query, (merchant_id,))

        stats = {}
        total_items = 0
        total_value = 0

        for result in results:
            item_type = result['item_type']
            stats[item_type] = {
                'item_count': result['item_count'],
                'total_quantity': result['total_quantity'],
                'avg_price': float(result['avg_price']) if result['avg_price'] else 0,
                'min_price': result['min_price'],
                'max_price': result['max_price']
            }
            total_items += result['item_count']
            total_value += result['total_quantity'] * (result['avg_price'] or 0)

        stats['_total'] = {
            'item_count': total_items,
            'total_value': total_value
        }

        return stats

    def get_merchant_all_items(self, floor_id: int) -> List[Dict[str, Any]]:
        """通过楼层ID获取所有商人库存（用于交易界面）"""
        query = """
        SELECT
            mi.id,
            mi.item_name,
            mi.item_type,
            mi.quantity,
            mi.price,
            mi.rarity_level,
            mi.effect_type,
            mi.effect_value,
            fm.merchant_name,
            fm.merchant_type
        FROM merchant_inventories mi
        INNER JOIN floor_merchants fm ON mi.merchant_id = fm.id
        WHERE fm.floor_id = %s AND fm.is_active = TRUE AND mi.quantity > 0
        ORDER BY mi.item_type, mi.price ASC
        """
        return self.execute_query(query, (floor_id,))

    def find_items_by_name(self, merchant_id: int, item_name: str) -> List[Dict[str, Any]]:
        """根据物品名称查找库存"""
        query = """
        SELECT * FROM merchant_inventories
        WHERE merchant_id = %s AND item_name LIKE %s AND quantity > 0
        ORDER BY price ASC
        """
        return self.execute_query(query, (merchant_id, f"%{item_name}%"))

    def get_price_range_items(self, merchant_id: int, min_price: int, max_price: int) -> List[Dict[str, Any]]:
        """获取指定价格区间的库存物品"""
        query = """
        SELECT * FROM merchant_inventories
        WHERE merchant_id = %s AND price BETWEEN %s AND %s AND quantity > 0
        ORDER BY price ASC
        """
        return self.execute_query(query, (merchant_id, min_price, max_price))