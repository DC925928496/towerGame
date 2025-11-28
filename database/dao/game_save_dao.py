"""
游戏存档数据访问对象
处理游戏存档的数据库操作
"""
from typing import List, Dict, Any, Optional
from database.dao.base_dao import BaseDAO
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GameSaveDAO(BaseDAO):
    """游戏存档数据访问对象"""

    def create(self, data: Dict[str, Any]) -> int:
        """创建游戏存档"""
        query = """
        INSERT INTO game_saves (
            player_id, floor_level, save_name, is_active, created_at, updated_at
        ) VALUES (
            %(player_id)s, %(floor_level)s, %(save_name)s, %(is_active)s, NOW(), NOW()
        )
        """
        return self.execute_insert(query, data)

    def get_by_id(self, save_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取存档信息"""
        query = """
        SELECT gs.*, p.name as player_name, p.level as player_level
        FROM game_saves gs
        INNER JOIN players p ON gs.id = p.id
        WHERE gs.id = %s
        """
        result = self.execute_query(query, (save_id,))
        return result[0] if result else None

    def update(self, save_id: int, data: Dict[str, Any]) -> bool:
        """更新存档信息"""
        set_clauses = []
        params = []

        for key, value in data.items():
            if key != 'id':
                set_clauses.append(f"{key} = %s")
                params.append(value)

        if not set_clauses:
            return False

        set_clauses.append("updated_at = NOW()")
        params.append(save_id)

        query = f"UPDATE game_saves SET {', '.join(set_clauses)} WHERE id = %s"
        return self.execute_update(query, params) > 0

    def delete(self, save_id: int) -> bool:
        """删除存档"""
        query = "DELETE FROM game_saves WHERE id = %s"
        return self.execute_update(query, (save_id,)) > 0

    def get_all_saves(self, player_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取所有存档列表"""
        if player_id:
            query = """
            SELECT gs.*, p.name as player_name, p.level as player_level
            FROM game_saves gs
            INNER JOIN players p ON gs.player_id = p.id
            WHERE gs.player_id = %s
            ORDER BY gs.updated_at DESC
            """
            return self.execute_query(query, (player_id,))
        else:
            query = """
            SELECT gs.*, p.name as player_name, p.level as player_level
            FROM game_saves gs
            INNER JOIN players p ON gs.player_id = p.id
            ORDER BY gs.updated_at DESC
            """
            return self.execute_query(query)

    def get_latest_save(self, player_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """获取最新存档"""
        if player_id:
            query = """
            SELECT gs.*, p.name as player_name
            FROM game_saves gs
            INNER JOIN players p ON gs.player_id = p.id
            WHERE gs.player_id = %s
            ORDER BY gs.updated_at DESC
            LIMIT 1
            """
            result = self.execute_query(query, (player_id,))
            return result[0] if result else None
        else:
            query = """
            SELECT gs.*, p.name as player_name
            FROM game_saves gs
            INNER JOIN players p ON gs.player_id = p.id
            ORDER BY gs.updated_at DESC
            LIMIT 1
            """
            result = self.execute_query(query)
            return result[0] if result else None

    def save_game_state(self, player_id: int, floor_level: int, save_name: str = None) -> int:
        """保存游戏状态"""
        if not save_name:
            save_name = f"存档_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        data = {
            'player_id': player_id,
            'floor_level': floor_level,
            'save_name': save_name,
            'is_active': True
        }

        return self.create(data)

    def deactivate_all_saves(self, player_id: int) -> bool:
        """停用玩家的所有存档"""
        query = "UPDATE game_saves SET is_active = FALSE WHERE player_id = %s"
        return self.execute_update(query, (player_id,)) > 0

    def get_save_count(self, player_id: Optional[int] = None) -> int:
        """获取存档数量"""
        if player_id:
            query = "SELECT COUNT(*) as count FROM game_saves WHERE player_id = %s"
            result = self.execute_query(query, (player_id,))
        else:
            query = "SELECT COUNT(*) as count FROM game_saves"
            result = self.execute_query(query)

        return result[0]['count'] if result else 0

    def get_saves_by_floor_range(self, min_floor: int, max_floor: int) -> List[Dict[str, Any]]:
        """获取指定楼层范围的存档"""
        query = """
        SELECT gs.*, p.name as player_name, p.level as player_level
        FROM game_saves gs
        INNER JOIN players p ON gs.player_id = p.id
        WHERE gs.floor_level BETWEEN %s AND %s
        ORDER BY gs.floor_level DESC, gs.updated_at DESC
        """
        return self.execute_query(query, (min_floor, max_floor))