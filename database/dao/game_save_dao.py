"""
游戏存档数据访问对象
处理游戏存档的数据库操作
"""
from typing import List, Dict, Any, Optional
from database.dao.base_dao import BaseDAO
from database.models import GameSaveModel
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

    # ========== GameSaveModel 集成方法 ==========

    def create_from_model(self, game_save: GameSaveModel) -> int:
        """
        从GameSaveModel创建存档记录

        Args:
            game_save: GameSaveModel实例

        Returns:
            新创建的存档ID
        """
        # 验证GameSaveModel
        if not game_save.is_valid():
            errors = game_save.validate()
            raise ValueError(f"GameSaveModel验证失败: {errors}")

        # 转换为字典
        save_data = game_save.to_dict()

        # 移除不应该插入的字段
        if 'id' in save_data:
            del save_data['id']
        if 'created_at' in save_data:
            del save_data['created_at']
        if 'updated_at' in save_data:
            del save_data['updated_at']

        return self.create(save_data)

    def get_by_model(self, save_id: int) -> Optional[GameSaveModel]:
        """
        获取GameSaveModel实例

        Args:
            save_id: 存档ID

        Returns:
            GameSaveModel实例或None
        """
        save_data = self.get_by_id(save_id)
        if not save_data:
            return None

        return GameSaveModel.from_dict(save_data)

    def get_by_player_as_model(self, player_id: int) -> List[GameSaveModel]:
        """
        获取指定玩家的所有存档

        Args:
            player_id: 玩家ID

        Returns:
            GameSaveModel列表
        """
        saves_data = self.get_by_player(player_id)
        return [GameSaveModel.from_dict(save_data) for save_data in saves_data]

    def get_active_save_as_model(self, player_id: int) -> Optional[GameSaveModel]:
        """
        获取玩家的活跃存档

        Args:
            player_id: 玩家ID

        Returns:
            活跃的GameSaveModel或None
        """
        save_data = self.get_active_save(player_id)
        if not save_data:
            return None

        return GameSaveModel.from_dict(save_data)

    def validate_game_save_model(self, game_save: GameSaveModel, skip_foreign_keys: bool = False) -> bool:
        """
        验证GameSaveModel

        Args:
            game_save: 要验证的GameSaveModel实例
            skip_foreign_keys: 是否跳过外键验证

        Returns:
            是否验证通过
        """
        return game_save.is_valid(skip_foreign_keys=skip_foreign_keys)

    def get_save_validation_summary(self, game_save: GameSaveModel) -> Dict[str, Any]:
        """
        获取GameSaveModel验证摘要

        Args:
            game_save: GameSaveModel实例

        Returns:
            验证摘要信息
        """
        return game_save.get_validation_summary()

