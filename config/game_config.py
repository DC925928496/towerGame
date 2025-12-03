"""
配置管理模块

提供游戏配置的统一管理，消除硬编码
"""

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class GameConfig:
    """游戏配置类，统一管理所有游戏参数"""

    # 基础游戏配置
    MAX_FLOORS: int = 100
    GRID_SIZE: int = 15
    ROOM_COUNT_MIN: int = 4
    ROOM_COUNT_MAX: int = 6
    ROOM_SIZE_MIN: int = 3
    ROOM_SIZE_MAX: int = 6
    GRID_CELL_PIXEL: int = 30
    CANVAS_WIDTH: int = None
    CANVAS_HEIGHT: int = None

    # 玩家初始属性/背包
    PLAYER_BASE_HP: int = 500
    PLAYER_BASE_ATK: int = 50
    PLAYER_BASE_DEF: int = 20
    PLAYER_BASE_GOLD: int = 0
    PLAYER_START_POTION_HEAL: int = 200
    PLAYER_START_POTION_COUNT: int = 3
    POTION_NAME: str = "血瓶"
    POTION_NAME_DELIMITER: str = "+"

    # 怪物配置
    MONSTER_BASE_HP: int = 80
    MONSTER_HP_PER_FLOOR: int = 20
    MONSTER_HP_VARIANCE: float = 0.2
    MONSTER_BASE_ATK: int = 25
    MONSTER_ATK_PER_FLOOR: int = 5
    MONSTER_ATK_VARIANCE: float = 0.2
    MONSTER_BASE_DEF: int = 12
    MONSTER_DEF_PER_FLOOR: int = 2
    MONSTER_DEF_VARIANCE: float = 0.2
    MONSTER_BASE_EXP: int = 20
    MONSTER_EXP_PER_FLOOR: int = 5
    MONSTER_BASE_GOLD: int = 14
    MONSTER_GOLD_PER_FLOOR: int = 4
    MONSTER_GOLD_VARIANCE: float = 0.15
    MONSTER_COUNT_BASE: int = 3
    MONSTER_COUNT_DIVISOR: int = 5

    # 道具/装备生成
    POTION_BASE_HEAL: int = 120
    POTION_HEAL_PER_FLOOR: int = 18
    WEAPON_BASE_ATK: int = 10
    WEAPON_ATK_PER_FLOOR: int = 3
    ARMOR_BASE_DEF: int = 4
    ARMOR_DEF_PER_FLOOR: int = 2

    # 物品生成权重
    ITEM_WEIGHTS: Dict[str, float] = None
    WEAPON_WEIGHT: float = 0.4
    ARMOR_WEIGHT: float = 0.35
    POTION_WEIGHT: float = 0.25
    STAIR_WEIGHT: float = 0.3

    # 守卫系统配置
    GUARD_WEIGHT_MULTIPLIER: float = 2.0
    GUARD_DISTANCE_WEIGHT: float = 10.0
    GUARD_DISTANCE_PENALTY: int = 3
    GUARD_STAT_BOOST_MULTIPLIER: float = 1.2

    # 战斗配置
    MIN_DAMAGE: int = 1
    CRITICAL_HIT_CHANCE: float = 0.05
    CRITICAL_HIT_MULTIPLIER: float = 2.0

    # 商人楼层概率配置
    MERCHANT_FIRST_FLOOR: int = 10
    MERCHANT_BASE_CHANCE: float = 0.04
    MERCHANT_CHANCE_INCREMENT: float = 0.04
    MERCHANT_FORCE_INTERVAL: int = 15

    # 商人物价配置
    MERCHANT_BASE_PRICE: int = 30
    MERCHANT_PRICE_PER_FLOOR: int = 4
    MERCHANT_POTION_PRICE_MULTIPLIER: float = 1.0
    MERCHANT_WEAPON_PRICE_MULTIPLIER: float = 2.0
    MERCHANT_ARMOR_PRICE_MULTIPLIER: float = 1.6
    MERCHANT_POTION_RANGE: tuple = (3, 4)
    MERCHANT_WEAPON_RANGE: tuple = (2, 3)
    MERCHANT_ARMOR_RANGE: tuple = (2, 3)

    # 战略投放
    HIGH_VALUE_ITEM_INTERVAL: int = 6
    HIGH_VALUE_ITEM_BASE_CHANCE: float = 0.25
    HIGH_VALUE_ITEM_MAX: int = 2

    # 锻造配置
    FORGE_BASE_COST: int = 120
    FORGE_LEVEL_COST: int = 80
    FORGE_RARITY_COST_MULTIPLIER: Dict[str, float] = None
    FORGE_BASE_SUCCESS: float = 0.85
    FORGE_SUCCESS_DECAY: float = 0.1
    FORGE_MIN_SUCCESS: float = 0.25
    FORGE_RARITY_SUCCESS_BONUS: Dict[str, float] = None

    # 稀有度配置
    RARITY_SETTINGS: Dict[str, Dict[str, Any]] = None

    def __post_init__(self):
        """初始化后处理，设置默认值和计算属性"""
        if self.ITEM_WEIGHTS is None:
            self.ITEM_WEIGHTS = {
                'weapon': self.WEAPON_WEIGHT,
                'armor': self.ARMOR_WEIGHT,
                'potion': self.POTION_WEIGHT
            }

        if self.FORGE_RARITY_COST_MULTIPLIER is None:
            self.FORGE_RARITY_COST_MULTIPLIER = {
                'common': 1.0,
                'rare': 1.15,
                'epic': 1.35,
                'legendary': 1.6
            }

        if self.FORGE_RARITY_SUCCESS_BONUS is None:
            self.FORGE_RARITY_SUCCESS_BONUS = {
                'common': 0.0,
                'rare': 0.05,
                'epic': 0.1,
                'legendary': 0.15
            }

        if self.RARITY_SETTINGS is None:
            self.RARITY_SETTINGS = {
                'common': {
                    'name': '普通',
                    'color': '#ffffff',
                    'attr_count': 1,
                    'probability': 0.5,
                    'multiplier': 1.0,
                    'prefixes': ['普通的']
                },
                'rare': {
                    'name': '稀有',
                    'color': '#0080ff',
                    'attr_count': 2,
                    'probability': 0.3,
                    'multiplier': 1.15,
                    'prefixes': ['精良的', '锐利的']
                },
                'epic': {
                    'name': '史诗',
                    'color': '#800080',
                    'attr_count': 3,
                    'probability': 0.15,
                    'multiplier': 1.35,
                    'prefixes': ['史诗的', '强大的', '远古的']
                },
                'legendary': {
                    'name': '传说',
                    'color': '#ffd700',
                    'attr_count': 4,
                    'probability': 0.05,
                    'multiplier': 1.6,
                    'prefixes': ['传说的', '神圣的', '不朽的']
                }
            }

        # 自动计算画布尺寸
        if self.CANVAS_WIDTH is None:
            self.CANVAS_WIDTH = self.GRID_SIZE * self.GRID_CELL_PIXEL
        if self.CANVAS_HEIGHT is None:
            self.CANVAS_HEIGHT = self.GRID_SIZE * self.GRID_CELL_PIXEL

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        result = {}
        for key, value in self.__dict__.items():
            result[key] = value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameConfig':
        """从字典创建配置对象"""
        return cls(**data)


# 预定义的物品配置
ITEM_CONFIGS = {
    "小血瓶": {"hp": 50, "type": "potion", "value": 20, "weight": 0.4},
    "大血瓶": {"hp": 150, "type": "potion", "value": 50, "weight": 0.6},

    "木剑": {"atk": 5, "type": "weapon", "value": 10, "weight": 0.3},
    "铁剑": {"atk": 10, "type": "weapon", "value": 25, "weight": 0.3},
    "钢剑": {"atk": 15, "type": "weapon", "value": 50, "weight": 0.2},
    "魔法剑": {"atk": 20, "type": "weapon", "value": 100, "weight": 0.2},

    "布甲": {"def": 3, "type": "armor", "value": 10, "weight": 0.3},
    "皮甲": {"def": 6, "type": "armor", "value": 25, "weight": 0.3},
    "铁甲": {"def": 9, "type": "armor", "value": 50, "weight": 0.2},
    "魔法甲": {"def": 12, "type": "armor", "value": 100, "weight": 0.2},
}

# 颜色配置
COLORS = {
    'wall': '#8B4513',        # 棕色 - 墙壁
    'floor': '#F0F0F0',       # 浅灰色 - 地板
    'player': '#FF0000',      # 红色 - 玩家
    'monster': '#00FF00',     # 绿色 - 怪物
    'weapon': '#0000FF',      # 蓝色 - 武器
    'armor': '#800080',       # 紫色 - 防具
    'potion': '#FF00FF',      # 粉色 - 血瓶
    'stair': '#FFA500',       # 橙色 - 楼梯
    'text': '#000000',        # 黑色 - 文本
    'background': '#FFFFFF'   # 白色 - 背景
}

# 游戏难度配置
DIFFICULTY_SETTINGS = {
    'easy': {
        'MONSTER_SCALING_RATE': 1.1,
        'MONSTER_BASE_HP': 80,
        'MONSTER_BASE_ATK': 8,
        'WEAPON_WEIGHT': 0.5,
        'ARMOR_WEIGHT': 0.5
    },
    'normal': {
        'MONSTER_SCALING_RATE': 1.15,
        'MONSTER_BASE_HP': 100,
        'MONSTER_BASE_ATK': 10,
        'WEAPON_WEIGHT': 0.4,
        'ARMOR_WEIGHT': 0.4
    },
    'hard': {
        'MONSTER_SCALING_RATE': 1.2,
        'MONSTER_BASE_HP': 120,
        'MONSTER_BASE_ATK': 12,
        'WEAPON_WEIGHT': 0.3,
        'ARMOR_WEIGHT': 0.3
    }
}


class ConfigManager:
    """配置管理器，提供配置的加载、保存和修改功能"""

    def __init__(self, config: GameConfig = None):
        self.config = config or GameConfig()
        self.difficulty = 'normal'

    def get_config(self) -> GameConfig:
        """获取当前配置"""
        return self.config

    def set_difficulty(self, difficulty: str):
        """设置游戏难度"""
        if difficulty in DIFFICULTY_SETTINGS:
            self.difficulty = difficulty
            # 应用难度设置
            settings = DIFFICULTY_SETTINGS[difficulty]
            for key, value in settings.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

    def update_config(self, **kwargs):
        """更新配置参数"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def reset_to_default(self):
        """重置为默认配置"""
        self.config = GameConfig()
        self.difficulty = 'normal'

    def save_config_to_dict(self) -> Dict[str, Any]:
        """保存配置为字典"""
        return {
            'config': self.config.to_dict(),
            'difficulty': self.difficulty
        }

    def load_config_from_dict(self, data: Dict[str, Any]):
        """从字典加载配置"""
        if 'config' in data:
            self.config = GameConfig.from_dict(data['config'])
        if 'difficulty' in data:
            self.set_difficulty(data['difficulty'])


# 全局配置管理器实例
config_manager = ConfigManager()
