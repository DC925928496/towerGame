"""
玩家数据访问对象
处理玩家基础信息的数据库操作
"""
from typing import List, Dict, Any, Optional
from database.dao.base_dao import BaseDAO
from database.models import PlayerModel
from datetime import datetime
import json

import logging
logger = logging.getLogger(__name__)


class PlayerDAO(BaseDAO):
    """玩家数据访问对象"""

    def create(self, data: Dict[str, Any]) -> int:
        """创建新玩家记录"""
        # 检查是否包含认证字段
        auth_fields = []
        auth_values = []

        if 'password_hash' in data:
            auth_fields.append('password_hash')
            auth_values.append('%(password_hash)s')
        if 'salt' in data:
            auth_fields.append('salt')
            auth_values.append('%(salt)s')
        if 'nickname' in data:
            auth_fields.append('nickname')
            auth_values.append('%(nickname)s')

        # 构建SQL查询
        base_fields = [
            'name', 'hp', 'max_hp', 'attack', 'defense',
            'level', 'exp', 'gold'
        ]
        base_values = [
            '%(name)s', '%(hp)s', '%(max_hp)s', '%(attack)s', '%(defense)s',
            '%(level)s', '%(exp)s', '%(gold)s'
        ]

        all_fields = base_fields + auth_fields
        all_values = base_values + auth_values

        query = f"""
        INSERT INTO players (
            {', '.join(all_fields)}, created_at, updated_at
        ) VALUES (
            {', '.join(all_values)}, NOW(), NOW()
        )
        """
        return self.execute_insert(query, data)

    def get_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取玩家信息"""
        query = "SELECT * FROM players WHERE id = %s"
        result = self.execute_query(query, (player_id,))
        return result[0] if result else None

    # ============ 用户认��相关方法 ============

    def exists_by_name(self, name: str) -> bool:
        """检查用户名是否已存在"""
        query = "SELECT id FROM players WHERE name = %s LIMIT 1"
        result = self.execute_query(query, (name,))
        return len(result) > 0

    def get_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名获取玩家信息"""
        query = "SELECT * FROM players WHERE name = %s LIMIT 1"
        result = self.execute_query(query, (username,))
        return result[0] if result else None

    def get_by_nickname(self, nickname: str) -> Optional[Dict[str, Any]]:
        """根据昵称获取玩家信息"""
        query = "SELECT * FROM players WHERE nickname = %s LIMIT 1"
        result = self.execute_query(query, (nickname,))
        return result[0] if result else None

    def update_last_login(self, player_id: int) -> bool:
        """更新最后登录时间"""
        query = "UPDATE players SET last_login = NOW() WHERE id = %s"
        return self.execute_update(query, (player_id,)) > 0

    def increment_login_attempts(self, player_id: int) -> bool:
        """增加登录失败次数"""
        query = "UPDATE players SET login_attempts = login_attempts + 1 WHERE id = %s"
        return self.execute_update(query, (player_id,)) > 0

    def reset_login_attempts(self, player_id: int) -> bool:
        """重置登录失败次数"""
        query = "UPDATE players SET login_attempts = 0, locked_until = NULL WHERE id = %s"
        return self.execute_update(query, (player_id,)) > 0

    def lock_account(self, player_id: int, lock_hours: int = 1) -> bool:
        """锁定账户"""
        query = "UPDATE players SET locked_until = DATE_ADD(NOW(), INTERVAL %s HOUR) WHERE id = %s"
        return self.execute_update(query, (lock_hours, player_id)) > 0

    def update_password(self, player_id: int, password_hash: str, salt: str) -> bool:
        """更新用户密码"""
        query = """
        UPDATE players
        SET password_hash = %s, salt = %s, updated_at = NOW()
        WHERE id = %s
        """
        return self.execute_update(query, (password_hash, salt, player_id)) > 0

    def get_active_sessions_count(self, player_id: int) -> int:
        """获取用户的活跃会话数量"""
        query = """
        SELECT COUNT(*) as session_count
        FROM user_sessions
        WHERE player_id = %s AND is_active = TRUE AND expires_at > NOW()
        """
        result = self.execute_query(query, (player_id,))
        return result[0]['session_count'] if result else 0

    def create_player_with_auth(self, name: str, password_hash: str, salt: str, nickname: str = 'gamer',
                              hp: int = 500, max_hp: int = 500, attack: int = 50,
                              defense: int = 20, level: int = 1, exp: int = 0,
                              gold: int = 0) -> int:
        """创建带认证信息的玩家记录"""
        data = {
            'name': name,
            'password_hash': password_hash,
            'salt': salt,
            'nickname': nickname,
            'hp': hp,
            'max_hp': max_hp,
            'attack': attack,
            'defense': defense,
            'level': level,
            'exp': exp,
            'gold': gold
        }
        return self.create(data)

    def update_nickname(self, player_id: int, nickname: str) -> bool:
        """更新玩家昵称"""
        query = "UPDATE players SET nickname = %s, updated_at = NOW() WHERE id = %s"
        return self.execute_update(query, (nickname, player_id)) > 0

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
            'attack': player_data.get('attack'),  # 修复字段名
            'defense': player_data.get('defense'),
            'level': player_data.get('level'),
            'exp': player_data.get('exp'),
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



    # ========== PlayerModel 集成方法 ==========

    def create_from_model(self, player: PlayerModel) -> int:
        """
        从PlayerModel创建玩家记录

        Args:
            player: PlayerModel实例

        Returns:
            新创建的玩家ID
        """
        # 验证PlayerModel
        if not player.is_valid():
            errors = player.validate()
            raise ValueError(f"PlayerModel验证失败: {errors}")

        # 转换为字典
        player_data = player.to_dict()

        # 移除不应该插入的字段（如id、时间戳等）
        if 'id' in player_data:
            del player_data['id']
        if 'created_at' in player_data:
            del player_data['created_at']
        if 'updated_at' in player_data:
            del player_data['updated_at']

        return self.create(player_data)

    def get_by_model(self, player_id: int) -> Optional[PlayerModel]:
        """
        获取PlayerModel实例

        Args:
            player_id: 玩家ID

        Returns:
            PlayerModel实例或None
        """
        player_data = self.get_by_id(player_id)
        if not player_data:
            return None

        return PlayerModel.from_dict(player_data)

    def list_all_as_models(self, limit: int = 100, offset: int = 0) -> List[PlayerModel]:
        """
        获取所有玩家的PlayerModel列表

        Args:
            limit: 限制数量
            offset: 偏移量

        Returns:
            PlayerModel列表
        """
        players_data = self.list_all(limit=limit, offset=offset)
        return [PlayerModel.from_dict(player_data) for player_data in players_data]

