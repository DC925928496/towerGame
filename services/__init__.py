"""
服务层统一入口
提供所有服务对象的统一管理接口
"""
from .player_service import PlayerService
from .game_save_service import GameSaveService
from .merchant_service import MerchantService
from .auth_service import AuthService
from .equipment_service import EquipmentService
from .inventory_service import InventoryService
import logging

logger = logging.getLogger(__name__)


class ServiceManager:
    """服务层管理器"""

    def __init__(self):
        """初始化所有服务实例"""
        self.player_service = PlayerService()
        self.game_save_service = GameSaveService()
        self.merchant_service = MerchantService()
        self.auth_service = AuthService()
        self.equipment_service = EquipmentService()
        self.inventory_service = InventoryService()

    # 玩家相关服务
    @property
    def player(self) -> PlayerService:
        """玩家服务"""
        return self.player_service

    # 游戏存档相关服务
    @property
    def game_save(self) -> GameSaveService:
        """游戏存档服务"""
        return self.game_save_service

    # 商人相关服务
    @property
    def merchant(self) -> MerchantService:
        """商人服务"""
        return self.merchant_service

    # 认证相关服务
    @property
    def auth(self) -> AuthService:
        """认证服务"""
        return self.auth_service

    # 装备相关服务
    @property
    def equipment(self) -> EquipmentService:
        """装备服务"""
        return self.equipment_service

    # 背包道具相关服务
    @property
    def inventory(self) -> InventoryService:
        """背包道具服务"""
        return self.inventory_service

    def get_all_services(self):
        """获取所有服务实例"""
        return {
            'player': self.player_service,
            'game_save': self.game_save_service,
            'merchant': self.merchant_service,
            'auth': self.auth_service,
            'equipment': self.equipment_service,
            'inventory': self.inventory_service
        }

    def close_all_connections(self):
        """关闭所有服务的数据库连接"""
        try:
            from database.dao import dao_manager
            dao_manager.close_all_connections()
            logger.info("所有服务连接已关闭")
        except Exception as e:
            logger.error(f"关闭服务连接失败: {e}")


# 全局服务管理器实例
service_manager = ServiceManager()


# 导出所有服务类和管理器
__all__ = [
    'PlayerService',
    'GameSaveService',
    'MerchantService',
    'AuthService',
    'EquipmentService',
    'InventoryService',
    'ServiceManager',
    'service_manager'
]