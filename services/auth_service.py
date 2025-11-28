"""
用户认证服务
处理用户注册、登录、会话管理等相关业务逻辑
"""
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import re
import logging

from .base_service import BaseService

logger = logging.getLogger(__name__)


class AuthService(BaseService):
    """用户认证服务"""

    def __init__(self):
        super().__init__()
        # JWT配置 - 使用固定密钥以确保重启后token仍然有效
        self.token_secret = "tower_game_jwt_secret_key_2024_persistent"
        self.token_expiry_hours = 24
        self.max_login_attempts = 5
        self.account_lock_hours = 1

    def register_user(self, username: str, password: str, nickname: str) -> Dict[str, Any]:
        """
        用户注册

        Args:
            username: 用户名（3-20字符，字母数字下划线）
            password: 密码（至少6位）
            nickname: 玩家昵称（1-50字符）

        Returns:
            注册结果字典
        """
        # 输入验证
        self._validate_registration_input(username, password)
        nickname = (nickname or '').strip()
        self._validate_nickname(nickname)

        try:
            # 检查用户名是否已存在
            if self.dao_manager.player.exists_by_name(username):
                raise ValueError("用户名已存在")

            # 检查昵称是否已存在
            if self.dao_manager.player.get_by_nickname(nickname):
                raise ValueError("该昵称已被其他用户使用")

            # 生成盐值和密码哈希
            salt = secrets.token_hex(16)
            password_hash = self._hash_password(password, salt)

            # 创建用户记录，默认昵称为gamer
            player_id = self.dao_manager.player.create_player_with_auth(
                name=username,
                password_hash=password_hash,
                salt=salt,
                nickname=nickname,
                hp=500,
                max_hp=500,
                attack=50,
                defense=20,
                level=1,
                exp=0,
                gold=0
            )

            # 记录注册日志
            self.dao_manager.login_log.create_log(
                player_id=player_id,
                username=username,
                login_type='register',
                reason='用户注册成功'
            )

            self.log_operation(f"用户注册成功: {username} (ID: {player_id})")

            return self.create_response(True, {
                'player_id': player_id,
                'username': username,
                'nickname': nickname
            }, "注册成功，请登录游戏")

        except ValueError as e:
            self.dao_manager.login_log.create_log(
                player_id=None,
                username=username,
                login_type='failed',
                reason=f'注册失败: {str(e)}'
            )
            raise
        except Exception as e:
            self.handle_error(e, "用户注册")

    def authenticate_user(self, username: str, password: str,
                         ip_address: str = None, user_agent: str = None) -> Dict[str, Any]:
        """
        用户认证登录

        Args:
            username: 用户名
            password: 密码
            ip_address: IP地址
            user_agent: 用户代理

        Returns:
            认证结果字典
        """
        try:
            # 输入验证
            if not username or not password:
                raise ValueError("请输入用户名和密码")

            # 获取用户信息
            player = self.dao_manager.player.get_by_username(username)
            if not player:
                self.dao_manager.login_log.create_log(
                    player_id=None,
                    username=username,
                    login_type='failed',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    reason='用户不存在'
                )
                raise ValueError("用户名或密码错误")

            # 检查账户是否被锁定
            if player.get('locked_until') and player['locked_until'] > datetime.now():
                self.dao_manager.login_log.create_log(
                    player_id=player['id'],
                    username=username,
                    login_type='failed',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    reason='账户被锁定'
                )
                raise ValueError("账户已被锁定，请稍后再试")

            # 检查失败登录次数
            if player.get('login_attempts', 0) >= self.max_login_attempts:
                if not player.get('locked_until'):
                    # 锁定账户
                    self.dao_manager.player.lock_account(player['id'], self.account_lock_hours)

                self.dao_manager.login_log.create_log(
                    player_id=player['id'],
                    username=username,
                    login_type='failed',
                    ip_address=ip_address,
                    user_agent=user_agent,
                    reason='登录次数过多，账户被锁定'
                )
                raise ValueError("登录失败次数过多，账户已被锁定")

            # 验证密码
            if not self._verify_password(password, player['password_hash'], player['salt']):
                self._handle_failed_login(player['id'], username, ip_address, user_agent)
                raise ValueError("用户名或密码错误")

            # 登录成功，重置失败次数
            self.dao_manager.player.reset_login_attempts(player['id'])

            # 检查是否已有活跃会话
            active_sessions = self.dao_manager.session.get_active_sessions_by_player(player['id'])
            if len(active_sessions) >= 3:  # 限制同时登录数量
                # 停用最旧的会话
                oldest_session = min(active_sessions, key=lambda x: x['created_at'])
                self.dao_manager.session.deactivate_session(oldest_session['id'])

            # 生成JWT令牌
            session_token = self._generate_session_token(player['id'])

            # 创建会话记录
            expires_at = datetime.now() + timedelta(hours=self.token_expiry_hours)
            self.dao_manager.session.create_session(
                player_id=player['id'],
                session_token=session_token,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # 更新最后登录时间
            self.dao_manager.player.update_last_login(player['id'])

            # 记录成功登录
            self.dao_manager.login_log.create_log(
                player_id=player['id'],
                username=username,
                login_type='success',
                ip_address=ip_address,
                user_agent=user_agent,
                reason='登录成功'
            )

            self.log_operation(f"用户登录成功: {player['name']} (ID: {player['id']})")

            return self.create_response(True, {
                'player_id': player['id'],
                'username': player['name'],
                'nickname': player.get('nickname', 'gamer'),
                'session_token': session_token,
                'expires_at': expires_at.isoformat(),
                'level': player.get('level', 1),
                'experience': player.get('experience', 0),
                'gold': player.get('gold', 0)
            }, "登录成功")

        except ValueError as e:
            raise
        except Exception as e:
            self.handle_error(e, "用户认证")

    def validate_session(self, session_token: str, websocket_session_id: str = None) -> Optional[Dict[str, Any]]:
        """
        验证会话有效性

        Args:
            session_token: JWT会话令牌
            websocket_session_id: WebSocket会话ID

        Returns:
            会话信息或None
        """
        try:
            if not session_token:
                return None

            # 检查JWT令牌有效性
            try:
                payload = jwt.decode(session_token, self.token_secret, algorithms=['HS256'])
                player_id = payload['player_id']
            except jwt.ExpiredSignatureError:
                logger.warning("JWT令牌已过期")
                return None
            except jwt.InvalidTokenError:
                logger.warning("无效的JWT令牌")
                return None

            # 检查数据库会话记录
            session = self.dao_manager.session.get_by_token(session_token)
            if not session or not session['is_active']:
                return None

            expires_at = session['expires_at']
            # 如果expires_at是字符串，需要转换为datetime
            if isinstance(expires_at, str):
                expires_at = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
            elif isinstance(expires_at, datetime) and expires_at.tzinfo is None:
                # 如果是naive datetime，假设它是系统时区
                pass

            if expires_at < datetime.now():
                self.dao_manager.session.deactivate_session(session['id'])
                return None

            # 更新WebSocket会话ID
            if websocket_session_id and session['websocket_session_id'] != websocket_session_id:
                self.dao_manager.session.update_websocket_session(session['id'], websocket_session_id)

            return session

        except Exception as e:
            logger.error(f"会话验证失败: {e}")
            return None

    def logout_user(self, session_token: str) -> bool:
        """
        用户登出

        Args:
            session_token: JWT会话令牌

        Returns:
            是否登出成功
        """
        try:
            session = self.dao_manager.session.get_by_token(session_token)
            if session:
                self.dao_manager.session.deactivate_session(session['id'])
                self.dao_manager.login_log.create_log(
                    player_id=session['player_id'],
                    username=session.get('player_name', ''),
                    login_type='logout',
                    reason='用户主动登出'
                )
                self.log_operation(f"用户登出: {session['player_name']} (ID: {session['player_id']})")
                return True
            return False
        except Exception as e:
            logger.error(f"用户登出失败: {e}")
            return False

    def extend_session(self, session_token: str, hours: int = 24) -> bool:
        """延长会话有效期"""
        try:
            return self.dao_manager.session.extend_session(session_token, hours)
        except Exception as e:
            logger.error(f"延长会话失败: {e}")
            return False

    def get_user_session_info(self, player_id: int) -> List[Dict[str, Any]]:
        """获取用户的所有会话信息"""
        try:
            return self.dao_manager.session.get_active_sessions_by_player(player_id)
        except Exception as e:
            logger.error(f"获取用户会话信息失败: {e}")
            return []

    def force_logout_all_sessions(self, player_id: int) -> int:
        """强制用户所有会话下线"""
        try:
            count = self.dao_manager.session.deactivate_all_player_sessions(player_id)
            if count > 0:
                self.dao_manager.login_log.create_log(
                    player_id=player_id,
                    username='',
                    login_type='logout',
                    reason='管理员强制下线'
                )
                self.log_operation(f"强制下线用户所有会话: ID {player_id}, 会话数: {count}")
            return count
        except Exception as e:
            logger.error(f"强制下线失败: {e}")
            return 0

    # ================== 私有方法 ==================

    def _validate_registration_input(self, username: str, password: str):
        """验证注册输入"""
        if not username or not password:
            raise ValueError("请填写所有必填字段")

        # 用户名验证：3-20字符，字母数字下划线，以字母开头
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{2,19}$', username):
            raise ValueError("用户名必须为3-20字符，以字母开头，只能包含字母、数字和下划线")

        # 密码验证：至少6位
        if len(password) < 6:
            raise ValueError("密码至少需要6位字符")

        # 密码强度检查（可选）
        if not re.search(r'[a-zA-Z]', password) or not re.search(r'\d', password):
            raise ValueError("密码必须包含字母和数字")

    def _validate_nickname(self, nickname: str):
        """验证昵称"""
        if not nickname or len(nickname.strip()) == 0:
            raise ValueError("昵称不能为空")

        nickname = nickname.strip()

        if len(nickname) > 50:
            raise ValueError("昵称长度不能超过50个字符")

    def _hash_password(self, password: str, salt: str) -> str:
        """密码哈希"""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        ).hex()

    def _verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """验证密码"""
        return self._hash_password(password, salt) == stored_hash

    def _generate_session_token(self, player_id: int) -> str:
        """生成JWT会话令牌"""
        now = datetime.now(timezone.utc)
        payload = {
            'player_id': player_id,
            'exp': now + timedelta(hours=self.token_expiry_hours),
            'iat': now
        }
        return jwt.encode(payload, self.token_secret, algorithm='HS256')

    def _handle_failed_login(self, player_id: int, username: str,
                           ip_address: str = None, user_agent: str = None):
        """处理登录失败"""
        # 增加失败次数
        self.dao_manager.player.increment_login_attempts(player_id)

        # 记录失败日志
        self.dao_manager.login_log.create_log(
            player_id=player_id,
            username=username,
            login_type='failed',
            ip_address=ip_address,
            user_agent=user_agent,
            reason='密码错误'
        )

        # 获取当前失败次数
        player = self.dao_manager.player.get_by_id(player_id)
        failed_attempts = player.get('login_attempts', 0) if player else 0

        # 如果达到最大失败次数，锁定账户
        if failed_attempts >= self.max_login_attempts:
            self.dao_manager.player.lock_account(player_id, self.account_lock_hours)
            logger.warning(f"账户因多次登录失败被锁定: {username}")

    def update_nickname(self, player_id: int, new_nickname: str) -> Dict[str, Any]:
        """
        更新用户昵称

        Args:
            player_id: 玩家ID
            new_nickname: 新昵称

        Returns:
            更新结果字典
        """
        try:
            # 验证昵称
            if not new_nickname or len(new_nickname.strip()) == 0:
                raise ValueError("昵称不能为空")

            new_nickname = new_nickname.strip()
            self._validate_nickname(new_nickname)

            # 检查昵称是否已被其他用户使用
            existing_player = self.dao_manager.player.get_by_nickname(new_nickname)
            if existing_player and existing_player['id'] != player_id:
                raise ValueError("该昵称已被其他用户使用")

            # 更新昵称
            success = self.dao_manager.player.update_nickname(player_id, new_nickname)
            if not success:
                raise ValueError("更新昵称失败")

            self.log_operation(f"用户 {player_id} 更新昵称为: {new_nickname}")

            return self.create_response(True, {
                'nickname': new_nickname
            }, "昵称更新成功")

        except ValueError as e:
            raise
        except Exception as e:
            self.handle_error(e, "更新昵称")

    def cleanup_expired_sessions(self):
        """清理过期会话"""
        try:
            count = self.dao_manager.session.cleanup_expired_sessions()
            if count > 0:
                self.log_operation(f"清理了 {count} 个过期会话")
            return count
        except Exception as e:
            logger.error(f"清理过期会话失败: {e}")
            return 0
