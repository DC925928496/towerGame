"""
用户会话数据访问对象
处理用户会话管理的数据库操作
"""
from typing import List, Dict, Any, Optional
from database.dao.base_dao import BaseDAO
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SessionDAO(BaseDAO):
    """用户会话数据访问对象"""

    # 实现抽象方法
    def create(self, data: Dict[str, Any]) -> int:
        """创建记录（基类方法，实际使用create_session）"""
        return self.create_session(
            player_id=data.get('player_id'),
            session_token=data.get('session_token'),
            expires_at=datetime.fromisoformat(data.get('expires_at')) if data.get('expires_at') else None,
            websocket_session_id=data.get('websocket_session_id'),
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent')
        )

    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取会话记录"""
        query = "SELECT * FROM user_sessions WHERE id = %s"
        result = self.execute_query(query, (record_id,))
        return result[0] if result else None

    def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """更新会话记录"""
        set_clauses = []
        params = []

        for key, value in data.items():
            if key != 'id':
                set_clauses.append(f"{key} = %s")
                params.append(value)

        if not set_clauses:
            return False

        params.append(record_id)
        query = f"UPDATE user_sessions SET {', '.join(set_clauses)} WHERE id = %s"
        return self.execute_update(query, params) > 0

    def delete(self, record_id: int) -> bool:
        """删除会话记录"""
        query = "DELETE FROM user_sessions WHERE id = %s"
        return self.execute_update(query, (record_id,)) > 0

    def create_session(self, player_id: int, session_token: str,
                      expires_at: datetime, websocket_session_id: str = None,
                      ip_address: str = None, user_agent: str = None) -> int:
        """创建新的用户会话"""
        data = {
            'player_id': player_id,
            'session_token': session_token,
            'websocket_session_id': websocket_session_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'expires_at': expires_at
        }

        query = """
        INSERT INTO user_sessions (
            player_id, session_token, websocket_session_id, ip_address, user_agent, expires_at
        ) VALUES (
            %(player_id)s, %(session_token)s, %(websocket_session_id)s,
            %(ip_address)s, %(user_agent)s, %(expires_at)s
        )
        """
        return self.execute_insert(query, data)

    def get_by_token(self, session_token: str) -> Optional[Dict[str, Any]]:
        """根据会话令牌获取会话信息"""
        query = """
        SELECT s.*, p.name as player_name
        FROM user_sessions s
        INNER JOIN players p ON s.player_id = p.id
        WHERE s.session_token = %s AND s.is_active = TRUE
        """
        result = self.execute_query(query, (session_token,))
        return result[0] if result else None

    def get_active_sessions_by_player(self, player_id: int) -> List[Dict[str, Any]]:
        """获取玩家的所有活跃会话"""
        query = """
        SELECT * FROM user_sessions
        WHERE player_id = %s AND is_active = TRUE AND expires_at > NOW()
        ORDER BY created_at DESC
        """
        return self.execute_query(query, (player_id,))

    def update_websocket_session(self, session_id: int, websocket_session_id: str) -> bool:
        """更新WebSocket会话ID"""
        query = """
        UPDATE user_sessions
        SET websocket_session_id = %s
        WHERE id = %s
        """
        return self.execute_update(query, (websocket_session_id, session_id)) > 0

    def deactivate_session(self, session_id: int) -> bool:
        """停用会话"""
        query = "UPDATE user_sessions SET is_active = FALSE WHERE id = %s"
        return self.execute_update(query, (session_id,)) > 0

    def deactivate_session_by_token(self, session_token: str) -> bool:
        """根据令牌停用会话"""
        query = "UPDATE user_sessions SET is_active = FALSE WHERE session_token = %s"
        return self.execute_update(query, (session_token,)) > 0

    def deactivate_all_player_sessions(self, player_id: int) -> int:
        """停用玩家的所有会话"""
        query = "UPDATE user_sessions SET is_active = FALSE WHERE player_id = %s"
        return self.execute_update(query, (player_id,))

    def extend_session(self, session_token: str, hours: int = 24) -> bool:
        """延长会话有效期"""
        query = """
        UPDATE user_sessions
        SET expires_at = DATE_ADD(expires_at, INTERVAL %s HOUR)
        WHERE session_token = %s AND is_active = TRUE
        """
        return self.execute_update(query, (hours, session_token)) > 0

    def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        query = """
        UPDATE user_sessions
        SET is_active = FALSE
        WHERE expires_at < NOW() OR is_active = FALSE
        """
        return self.execute_update(query)

    def get_session_count_by_player(self, player_id: int) -> int:
        """获取玩家的会话数量"""
        query = """
        SELECT COUNT(*) as session_count
        FROM user_sessions
        WHERE player_id = %s AND is_active = TRUE AND expires_at > NOW()
        """
        result = self.execute_query(query, (player_id,))
        return result[0]['session_count'] if result else 0

    def is_session_valid(self, session_token: str) -> bool:
        """检查会话是否有效"""
        query = """
        SELECT COUNT(*) as valid_count
        FROM user_sessions
        WHERE session_token = %s
        AND is_active = TRUE
        AND expires_at > NOW()
        """
        result = self.execute_query(query, (session_token,))
        return result[0]['valid_count'] > 0 if result else False

    def get_session_by_websocket_id(self, websocket_session_id: str) -> Optional[Dict[str, Any]]:
        """根据WebSocket会话ID获取会话信息"""
        query = """
        SELECT s.*, p.name as player_name
        FROM user_sessions s
        INNER JOIN players p ON s.player_id = p.id
        WHERE s.websocket_session_id = %s AND s.is_active = TRUE AND s.expires_at > NOW()
        """
        result = self.execute_query(query, (websocket_session_id,))
        return result[0] if result else None
