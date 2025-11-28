"""
玩家数据访问对象
处理玩家基础信息的数据库操作
"""
from typing import List, Dict, Any, Optional
from database.dao.base_dao import BaseDAO
from datetime import datetime
import json

import logging
logger = logging.getLogger(__name__)


class PlayerDAO(BaseDAO):
    """玩家数据访问对象"""

    def create(self, data: Dict[str, Any]) -> int:
        """创建新玩家记录"""
        query = """
        INSERT INTO players (
            name, hp, max_hp, atk, defense, level, exp, exp_needed,
            gold, weapon_name, weapon_atk, armor_name, armor_def,
            weapon_rarity, position_x, position_y, created_at, updated_at
        ) VALUES (
            %(name)s, %(hp)s, %(max_hp)s, %(atk)s, %(defense)s,
            %(level)s, %(exp)s, %(exp_needed)s, %(gold)s,
            %(weapon_name)s, %(weapon_atk)s, %(armor_name)s, %(armor_def)s,
            %(weapon_rarity)s, %(position_x)s, %(position_y)s, NOW(), NOW()
        )
        """
        return self.execute_insert(query, data)

    def get_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取玩家信息"""
        query = "SELECT * FROM players WHERE id = %s"
        result = self.execute_query(query, (player_id,))
        return result[0] if result else None

    def update(self, player_id: int, data: Dict[str, Any]) -> bool:
        """更新玩家信息"""
        set_clauses = []
        params = []

        for key, value in data.items():
            if key != 'id':  # 不更新ID
                set_clauses.append(f"{key} = %s")
                params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = NOW()")
        params.append(player_id)

        query = f"UPDATE players SET {', '.join(set_clauses)} WHERE id = %s"
        return self.execute_update(query, params) > 0

    def delete(self, player_id: int) -> bool:
        """删除玩家记录"""
        query = "DELETE FROM players WHERE id = %s"
        return self.execute_update(query, (player_id,)) > 0

    def get_by_save_id(self, save_id: int) -> Optional[Dict[str, Any]]:
        """根据存档ID获取玩家信息"""
        query = """
        SELECT p.* FROM players p
        INNER JOIN game_saves gs ON p.id = gs.player_id
        WHERE gs.id = %s
        """
        result = self.execute_query(query, (save_id,))
        return result[0] if result else None

    def get_latest_player(self) -> Optional[Dict[str, Any]]:
        """获取最新创建的玩家"""
        query = "SELECT * FROM players ORDER BY created_at DESC LIMIT 1"
        result = self.execute_query(query)
        return result[0] if result else None

    def update_player_state(self, player_id: int, player_data: Dict[str, Any]) -> bool:
        """更新玩家游戏状态"""
        update_data = {
            'hp': player_data.get('hp'),
            'max_hp': player_data.get('max_hp'),
            'atk': player_data.get('atk'),
            'defense': player_data.get('defense'),
            'level': player_data.get('level'),
            'exp': player_data.get('exp'),
            'exp_needed': player_data.get('exp_needed'),
            'gold': player_data.get('gold'),
            'weapon_name': player_data.get('weapon_name'),
            'weapon_atk': player_data.get('weapon_atk'),
            'armor_name': player_data.get('armor_name'),
            'armor_def': player_data.get('armor_def'),
            'weapon_rarity': player_data.get('weapon_rarity'),
            'position_x': player_data.get('position', {}).get('x'),
            'position_y': player_data.get('position', {}).get('y')
        }

        return self.update(player_id, update_data)

    def get_player_stats(self, player_id: int) -> Optional[Dict[str, Any]]:
        """获取玩家统计信息"""
        query = """
        SELECT
            p.*,
            COUNT(pe.id) as equipment_count,
            COUNT(pi.id) as inventory_count,
            (SELECT COUNT(*) FROM saved_floors sf WHERE sf.player_id = p.id) as floor_count
        FROM players p
        LEFT JOIN player_equipment pe ON p.id = pe.player_id
        LEFT JOIN player_inventory pi ON p.id = pi.player_id
        WHERE p.id = %s
        GROUP BY p.id
        """
        result = self.execute_query(query, (player_id,))
        return result[0] if result else None