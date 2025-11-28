"""
登录日志数据访问对象
处理用户登录日志的数据库操作
"""
from typing import List, Dict, Any, Optional
from database.dao.base_dao import BaseDAO
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class LoginLogDAO(BaseDAO):
    """登录日志数据访问对象"""

    # 实现抽象方法
    def create(self, data: Dict[str, Any]) -> int:
        """创建记录（基类方法，实际��用create_log）"""
        return self.create_log(
            player_id=data.get('player_id'),
            username=data.get('username', ''),
            login_type=data.get('login_type', 'failed'),
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent'),
            reason=data.get('reason')
        )

    def get_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取登录日志记录"""
        query = "SELECT * FROM login_logs WHERE id = %s"
        result = self.execute_query(query, (record_id,))
        return result[0] if result else None

    def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """更新登录日志记录"""
        set_clauses = []
        params = []

        for key, value in data.items():
            if key != 'id':
                set_clauses.append(f"{key} = %s")
                params.append(value)

        if not set_clauses:
            return False

        params.append(record_id)
        query = f"UPDATE login_logs SET {', '.join(set_clauses)} WHERE id = %s"
        return self.execute_update(query, params) > 0

    def delete(self, record_id: int) -> bool:
        """删除登录日志记录"""
        query = "DELETE FROM login_logs WHERE id = %s"
        return self.execute_update(query, (record_id,)) > 0

    def create_log(self, player_id: Optional[int], username: str,
                   login_type: str, ip_address: str = None,
                   user_agent: str = None, reason: str = None) -> int:
        """创建登录日志"""
        data = {
            'player_id': player_id,
            'username': username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'login_type': login_type,
            'reason': reason
        }

        query = """
        INSERT INTO login_logs (
            player_id, username, ip_address, user_agent, login_type, reason
        ) VALUES (
            %(player_id)s, %(username)s, %(ip_address)s, %(user_agent)s, %(login_type)s, %(reason)s
        )
        """
        return self.execute_insert(query, data)

    def get_player_login_logs(self, player_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """获取玩家的登录日志"""
        query = """
        SELECT * FROM login_logs
        WHERE player_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """
        return self.execute_query(query, (player_id, limit))

    def get_recent_failed_attempts(self, username: str, hours: int = 1) -> int:
        """获取最近指定小时内的登录失败次数"""
        query = """
        SELECT COUNT(*) as failed_count
        FROM login_logs
        WHERE username = %s
        AND login_type = 'failed'
        AND created_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        """
        result = self.execute_query(query, (username, hours))
        return result[0]['failed_count'] if result else 0

    def get_ip_login_attempts(self, ip_address: str, minutes: int = 15) -> int:
        """获取指定IP在最近分钟内的登录尝试次数"""
        query = """
        SELECT COUNT(*) as attempt_count
        FROM login_logs
        WHERE ip_address = %s
        AND created_at >= DATE_SUB(NOW(), INTERVAL %s MINUTE)
        """
        result = self.execute_query(query, (ip_address, minutes))
        return result[0]['attempt_count'] if result else 0

    def get_login_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取登录统计信息"""
        query = """
        SELECT
            COUNT(*) as total_logins,
            COUNT(CASE WHEN login_type = 'success' THEN 1 END) as successful_logins,
            COUNT(CASE WHEN login_type = 'failed' THEN 1 END) as failed_logins,
            COUNT(CASE WHEN login_type = 'register' THEN 1 END) as registrations,
            COUNT(DISTINCT player_id) as unique_players,
            COUNT(DISTINCT ip_address) as unique_ips
        FROM login_logs
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        result = self.execute_query(query, (days,))
        return result[0] if result else {}

    def get_daily_login_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """获取每日登录统计"""
        query = """
        SELECT
            DATE(created_at) as date,
            COUNT(*) as total_logins,
            COUNT(CASE WHEN login_type = 'success' THEN 1 END) as successful_logins,
            COUNT(CASE WHEN login_type = 'failed' THEN 1 END) as failed_logins,
            COUNT(CASE WHEN login_type = 'register' THEN 1 END) as registrations,
            COUNT(DISTINCT player_id) as unique_players
        FROM login_logs
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        """
        return self.execute_query(query, (days,))

    def get_suspicious_activities(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取可疑活动（多次失败登录等）"""
        query = """
        SELECT
            username,
            ip_address,
            COUNT(*) as failed_attempts,
            MAX(created_at) as last_attempt,
            GROUP_CONCAT(DISTINCT reason) as failure_reasons
        FROM login_logs
        WHERE login_type = 'failed'
        AND created_at >= DATE_SUB(NOW(), INTERVAL %s HOUR)
        GROUP BY username, ip_address
        HAVING failed_attempts >= 3
        ORDER BY failed_attempts DESC, last_attempt DESC
        """
        return self.execute_query(query, (hours,))

    def cleanup_old_logs(self, days: int = 90) -> int:
        """清理旧的登录日志"""
        query = """
        DELETE FROM login_logs
        WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        return self.execute_update(query, (days,))

    def get_player_last_login(self, player_id: int) -> Optional[Dict[str, Any]]:
        """获取玩家最后登录信息"""
        query = """
        SELECT * FROM login_logs
        WHERE player_id = %s AND login_type = 'success'
        ORDER BY created_at DESC
        LIMIT 1
        """
        result = self.execute_query(query, (player_id,))
        return result[0] if result else None

    def is_account_locked(self, username: str) -> bool:
        """检查账户是否因多次失败登录而被锁定"""
        query = """
        SELECT COUNT(*) as failed_count
        FROM login_logs
        WHERE username = %s
        AND login_type = 'failed'
        AND created_at >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """
        result = self.execute_query(query, (username,))
        return (result[0]['failed_count'] if result else 0) >= 5
