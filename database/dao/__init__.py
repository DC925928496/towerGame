"""
DAO层统一入口
提供所有数据访问对象的统一管理接口
"""
from .player_dao import PlayerDAO
from .weapon_attribute_dao import WeaponAttributeDAO
from .game_save_dao import GameSaveDAO
from .equipment_dao import EquipmentDAO
from .floor_dao import FloorDAO
from .item_dao import ItemDAO
from .merchant_dao import MerchantDAO
from .merchant_inventory_dao import MerchantInventoryDAO


class DAOManager:
    """DAO层管理器"""

    def __init__(self):
        """初始化所有DAO实例"""
        self.player_dao = PlayerDAO()
        self.weapon_attribute_dao = WeaponAttributeDAO()
        self.game_save_dao = GameSaveDAO()
        self.equipment_dao = EquipmentDAO()
        self.floor_dao = FloorDAO()
        self.item_dao = ItemDAO()
        self.merchant_dao = MerchantDAO()
        self.merchant_inventory_dao = MerchantInventoryDAO()

    # 玩家相关DAO
    @property
    def player(self) -> PlayerDAO:
        """玩家DAO"""
        return self.player_dao

    # 武器属性相关DAO
    @property
    def weapon_attribute(self) -> WeaponAttributeDAO:
        """武器属性DAO"""
        return self.weapon_attribute_dao

    # 游戏存档相关DAO
    @property
    def game_save(self) -> GameSaveDAO:
        """游戏存档DAO"""
        return self.game_save_dao

    # 装备相关DAO
    @property
    def equipment(self) -> EquipmentDAO:
        """装备DAO"""
        return self.equipment_dao

    # 楼层相关DAO
    @property
    def floor(self) -> FloorDAO:
        """楼层DAO"""
        return self.floor_dao

    # 物品相关DAO
    @property
    def item(self) -> ItemDAO:
        """物品DAO"""
        return self.item_dao

    # 商人相关DAO
    @property
    def merchant(self) -> MerchantDAO:
        """商人DAO"""
        return self.merchant_dao

    # 商人库存相关DAO
    @property
    def merchant_inventory(self) -> MerchantInventoryDAO:
        """商人库存DAO"""
        return self.merchant_inventory_dao

    def get_all_daos(self):
        """获取所有DAO实例"""
        return {
            'player': self.player_dao,
            'weapon_attribute': self.weapon_attribute_dao,
            'game_save': self.game_save_dao,
            'equipment': self.equipment_dao,
            'floor': self.floor_dao,
            'item': self.item_dao,
            'merchant': self.merchant_dao,
            'merchant_inventory': self.merchant_inventory_dao
        }

    def close_all_connections(self):
        """关闭所有DAO的数据库连接"""
        for dao in self.get_all_daos().values():
            if hasattr(dao, 'close_connection'):
                dao.close_connection()


# 全局DAO管理器实例
dao_manager = DAOManager()


# 导出所有DAO类和管理器
__all__ = [
    'PlayerDAO',
    'WeaponAttributeDAO',
    'GameSaveDAO',
    'EquipmentDAO',
    'FloorDAO',
    'ItemDAO',
    'MerchantDAO',
    'MerchantInventoryDAO',
    'DAOManager',
    'dao_manager'
]