"""
玩家���包道具数据访问对象
处理玩家道具管理的数据库操作
"""
from typing import List, Dict, Any, Optional
from database.dao.base_dao import BaseDAO
from database.models import PlayerInventoryModel
import logging

logger = logging.getLogger(__name__)


class InventoryDAO(BaseDAO):
    """玩家背包道具数据访问对象"""

    # 实现抽象方法
    def create(self, data: Dict[str, Any]) -> int:
        """创建道具记录"""
        return self.add_item(
            player_id=data.get('player_id'),
            item_name=data.get('item_name'),
            quantity=data.get('quantity', 1)
        )

    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取道具记录"""
        query = "SELECT * FROM player_inventory WHERE id = %s"
        result = self.execute_query(query, (record_id,))
        return result[0] if result else None

    def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """更新道具记录"""
        set_clauses = []
        params = []

        for key, value in data.items():
            if key != 'id':
                set_clauses.append(f"{key} = %s")
                params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = NOW()")
        params.append(record_id)

        query = f"UPDATE player_inventory SET {', '.join(set_clauses)} WHERE id = %s"
        return self.execute_update(query, params) > 0

    def delete(self, record_id: int) -> bool:
        """删除道具记录"""
        query = "DELETE FROM player_inventory WHERE id = %s"
        return self.execute_update(query, (record_id,)) > 0

    def add_item(self, player_id: int, item_name: str, quantity: int = 1) -> int:
        """添加道具到背包"""
        # 检查是否已存在该道具
        existing = self.get_item(player_id, item_name)
        if existing:
            # 更新数量
            new_quantity = existing['quantity'] + quantity
            query = """
            UPDATE player_inventory
            SET quantity = %s, updated_at = NOW()
            WHERE id = %s
            """
            self.execute_update(query, (new_quantity, existing['id']))
            return existing['id']
        else:
            # 创建新记录
            query = """
            INSERT INTO player_inventory (player_id, item_name, quantity, created_at, updated_at)
            VALUES (%s, %s, %s, NOW(), NOW())
            """
            return self.execute_insert(query, (player_id, item_name, quantity))

    def get_item(self, player_id: int, item_name: str) -> Optional[Dict[str, Any]]:
        """获取玩家指定的道具"""
        query = """
        SELECT * FROM player_inventory
        WHERE player_id = %s AND item_name = %s
        LIMIT 1
        """
        result = self.execute_query(query, (player_id, item_name))
        return result[0] if result else None

    def get_player_inventory(self, player_id: int) -> List[Dict[str, Any]]:
        """获取玩家的所有道具"""
        query = """
        SELECT * FROM player_inventory
        WHERE player_id = %s
        ORDER BY created_at ASC
        """
        return self.execute_query(query, (player_id,))

    def consume_item(self, player_id: int, item_name: str, quantity: int = 1) -> bool:
        """消耗道具"""
        try:
            item = self.get_item(player_id, item_name)
            if not item or item['quantity'] < quantity:
                return False

            new_quantity = item['quantity'] - quantity
            if new_quantity <= 0:
                # 数量为0，删除记录
                query = "DELETE FROM player_inventory WHERE id = %s"
                return self.execute_update(query, (item['id'],)) > 0
            else:
                # 更新数量
                query = """
                UPDATE player_inventory
                SET quantity = %s, updated_at = NOW()
                WHERE id = %s
                """
                return self.execute_update(query, (new_quantity, item['id'])) > 0
        except Exception as e:
            logger.error(f"消耗道具失败: {e}")
            return False

    def update_item_quantity(self, player_id: int, item_name: str, quantity: int) -> bool:
        """更新道具数量"""
        try:
            if quantity <= 0:
                # 删除道具
                item = self.get_item(player_id, item_name)
                if item:
                    return self.delete(item['id'])
                return True
            else:
                # 更新数量
                item = self.get_item(player_id, item_name)
                if item:
                    query = """
                    UPDATE player_inventory
                    SET quantity = %s, updated_at = NOW()
                    WHERE id = %s
                    """
                    return self.execute_update(query, (quantity, item['id'])) > 0
                else:
                    # 创建新记录
                    self.add_item(player_id, item_name, quantity)
                    return True
        except Exception as e:
            logger.error(f"更新道具数量失败: {e}")
            return False

    def transfer_item(self, from_player_id: int, to_player_id: int, item_name: str, quantity: int) -> bool:
        """转移道具（用于交易等场景）"""
        try:
            # 检查源玩家是否有足够的道具
            from_item = self.get_item(from_player_id, item_name)
            if not from_item or from_item['quantity'] < quantity:
                return False

            # 从源玩家扣除
            if not self.consume_item(from_player_id, item_name, quantity):
                return False

            # 给目标玩家添加
            self.add_item(to_player_id, item_name, quantity)
            return True
        except Exception as e:
            logger.error(f"转移道具失败: {e}")
            return False

    def clear_inventory(self, player_id: int) -> bool:
        """清空玩家背包"""
        query = "DELETE FROM player_inventory WHERE player_id = %s"
        return self.execute_update(query, (player_id,)) > 0

    def get_inventory_summary(self, player_id: int) -> Dict[str, int]:
        """获取背包统计摘要"""
        query = """
        SELECT
            COUNT(*) as total_items,
            SUM(quantity) as total_quantity
        FROM player_inventory
        WHERE player_id = %s
        """
        result = self.execute_query(query, (player_id,))
        if result:
            return {
                'total_items': result[0]['total_items'] or 0,
                'total_quantity': result[0]['total_quantity'] or 0
            }
        return {'total_items': 0, 'total_quantity': 0}

    def get_items_by_type(self, player_id: int, item_type: str) -> List[Dict[str, Any]]:
        """根据道具类型获取道具（通过名称匹配）"""
        query = """
        SELECT * FROM player_inventory
        WHERE player_id = %s AND item_name LIKE %s
        ORDER BY created_at ASC
        """
        return self.execute_query(query, (player_id, f"%{item_type}%"))