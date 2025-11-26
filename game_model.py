from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional
import random

# 导入新的工具类和配置
from utils.position_utils import Position, PositionUtils
from utils.game_utils import GameUtils
from config.game_config import config_manager


# ==================== 基础数据类 ====================

# Position 类现在从 utils.position_utils 导入
# @dataclass
# class Position:
#     """二维坐标"""
#     x: int
#     y: int
#
#     def __add__(self, other: 'Position') -> 'Position':
#         return Position(self.x + other.x, self.y + other.y)
#
#     def __eq__(self, other: 'Position') -> bool:
#         return self.x == other.x and self.y == other.y
#
#     def __hash__(self):
#         return hash((self.x, self.y))
#
#     def __repr__(self):
#         return f"Position({self.x}, {self.y})"


class CellType(Enum):
    """地图格子类型枚举 - 使用配置符号"""
    # 从配置获取符号，保持向后兼容
    EMPTY = '.'  # 空地
    WALL = '#'   # 墙
    PLAYER = '@' # 玩家
    MONSTER = 'M'  # 怪物
    STAIRS = '>'   # 楼梯
    POTION = '+'   # 血瓶
    WEAPON = '↑'   # 武器
    ARMOR = '◆'    # 防具
    MERCHANT = '$'  # 商人


class Cell:
    """地图格子"""
    def __init__(self, cell_type: CellType, passable: bool = True, entity=None):
        self.type = cell_type
        self.passable = passable
        self.entity = entity  # 怪物或道具对象

    def __str__(self):
        if self.entity is not None:
            return self.entity.symbol
        return self.type.value


# ==================== 实体类 ====================

@dataclass
class Item:
    """道具类"""
    symbol: str
    name: str
    effect_type: str  # 'potion':血瓶, 'weapon':武器, 'armor':防具
    effect_value: int
    position: Position
    item_id: Optional[str] = None

    def __post_init__(self):
        if self.item_id is None:
            self.item_id = f"item_{random.randint(1000, 9999)}"

    def to_dict(self) -> dict:
        """将Item对象转换为可JSON序列化的字典"""
        return {
            'symbol': self.symbol,
            'name': self.name,
            'effect_type': self.effect_type,
            'effect_value': self.effect_value,
            'item_id': self.item_id
        }


class Monster:
    """怪物类"""
    def __init__(self, monster_id: str, name: str, hp: int, atk: int, defense: int,
                 exp: int, gold: int, position: Position):
        self.id = monster_id
        self.name = name
        self.hp = hp
        self.max_hp = hp
        self.atk = atk
        self.defense = defense
        self.exp = exp
        self.gold = gold
        self.position = position
        self.symbol = 'M'

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, damage: int) -> int:
        """受到伤害，返回实际造成的伤害"""
        actual_damage = max(1, damage - self.defense)
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage


class Player:
    """玩家类"""
    def __init__(self):
        self.hp = 500
        self.max_hp = 500
        self.atk = 50
        self.defense = 20
        self.exp = 0
        self.level = 1
        self.gold = 0
        self.position = Position(7, 7)

        # 装备
        self.weapon_atk = 0
        self.weapon_name = None
        self.armor_def = 0
        self.armor_name = None

        # 背包：{道具名: 数量}
        self.inventory = {"小血瓶": 3}

    @property
    def total_atk(self) -> int:
        """总攻击力 = 基础 + 武器加成"""
        return self.atk + self.weapon_atk

    @property
    def total_def(self) -> int:
        """总防御力 = 基础 + 防具加成"""
        return self.defense + self.armor_def

    @property
    def exp_needed(self) -> int:
        """升级所需经验"""
        return self.level * 100

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, damage: int) -> int:
        """受到伤害，返回实际受到的伤害"""
        actual_damage = max(1, damage - self.total_def)
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage

    def heal(self, amount: int):
        """治疗"""
        old_hp = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        healed = self.hp - old_hp
        return healed

    def gain_exp(self, exp: int) -> List[str]:
        """获得经验，返回升级日志"""
        logs = []
        self.exp += exp

        while self.exp >= self.exp_needed:
            self.exp -= self.exp_needed
            self.level_up(logs)

        return logs

    def level_up(self, logs: List[str]):
        """升级"""
        self.level += 1
        self.max_hp += 50
        self.hp = self.max_hp  # 回满血
        self.atk += 5
        self.defense += 3

        logs.append(f"升级了！Lv.{self.level}，max_hp+50，atk+5，def+3")

    def use_item(self, item_name: str) -> Optional[str]:
        """使用背包道具，返回日志消息"""
        if item_name not in self.inventory or self.inventory[item_name] <= 0:
            return None

        if item_name == "小血瓶":
            healed = self.heal(200)
            self.inventory[item_name] -= 1
            if self.inventory[item_name] == 0:
                del self.inventory[item_name]
            return f"使用了小血瓶，回复了 {healed} 点生命值"

        return None

    def get_inventory_list(self) -> List[tuple]:
        """获取背包列表，格式: [(道具名, 数量), ...]"""
        return list(self.inventory.items())


class Room:
    """房间类，用于地图生成"""
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def center(self) -> Position:
        """房间中心坐标"""
        return Position(self.x + self.width // 2, self.y + self.height // 2)

    def intersects(self, other: 'Room') -> bool:
        """检查是否与其他房间重叠"""
        return not (self.x + self.width < other.x or
                    other.x + other.width < self.x or
                    self.y + self.height < other.y or
                    other.y + other.height < self.y)


# ==================== 商人系统 ====================

@dataclass
class MerchantItem:
    """商人出售的物品"""
    name: str
    effect_type: str  # potion/weapon/armor
    effect_value: int
    price: int


class Merchant:
    """商人类"""
    def __init__(self, position: Position, inventory: List[MerchantItem], name: str = "神秘商人"):
        self.position = position
        self.inventory = inventory
        self.name = name
        self.symbol = '$'


# ==================== 楼层类 ====================

class Floor:
    """楼层类（15×15地图）"""
    def __init__(self, level: int, width: int = 15, height: int = 15):
        self.level = level
        self.width = width
        self.height = height

        # 二维地图格子
        self.grid: List[List[Cell]] = [
            [Cell(CellType.WALL, passable=False) for _ in range(width)]
            for _ in range(height)
        ]

        self.monsters: Dict[str, Monster] = {}  # {monster_id: Monster}
        self.items: Dict[str, Item] = {}        # {item_id: Item}

        self.stairs_pos: Optional[Position] = None
        self.player_start_pos: Optional[Position] = None

        # 商人楼层相关
        self.is_merchant_floor: bool = False
        self.merchant: Optional[Merchant] = None

    def get_cell(self, pos: Position) -> Optional[Cell]:
        """获取指定位置的格子"""
        if 0 <= pos.x < self.width and 0 <= pos.y < self.height:
            return self.grid[pos.x][pos.y]
        return None

    def set_cell(self, pos: Position, cell: Cell):
        """设置指定位置的格子"""
        if 0 <= pos.x < self.width and 0 <= pos.y < self.height:
            self.grid[pos.x][pos.y] = cell

    def is_passable(self, pos: Position) -> bool:
        """判断位置是否可通行 - 允许道具但阻止怪物"""
        cell = self.get_cell(pos)
        if cell is None:
            return False
        if not cell.passable:
            return False
        # 允许道具（可交互实体）
        if cell.entity and hasattr(cell.entity, 'effect_type'):  # 是道具
            return True
        # 阻止怪物和其他实体
        if cell.entity is not None:
            return False
        return True

    def get_monster_at(self, pos: Position) -> Optional[Monster]:
        """获取指定位置的怪物"""
        for monster in self.monsters.values():
            if monster.position == pos:
                return monster
        return None

    def get_item_at(self, pos: Position) -> Optional[Item]:
        """获取指定位置的道具"""
        for item in self.items.values():
            if item.position == pos:
                return item
        return None

    def remove_item(self, item_id: str, clear_entity: bool = True):
        """
        移除道具

        Args:
            item_id: 道具ID
            clear_entity: 是否清除地图格子的实体（用于装备替换时避免冲突）
        """
        if item_id in self.items:
            item = self.items[item_id]
            pos = item.position
            if clear_entity:
                self.grid[pos.x][pos.y].entity = None
            del self.items[item_id]

    def remove_monster(self, monster_id: str):
        """移除怪物"""
        if monster_id in self.monsters:
            monster = self.monsters[monster_id]
            pos = monster.position
            self.grid[pos.x][pos.y].entity = None
            del self.monsters[monster_id]

    def get_connected_area(self, start_pos: Position) -> List[Position]:
        """
        使用Flood Fill算法获取从指定位置开始的连通区域（房间）
        只包含可通行的空地

        Args:
            start_pos: 起始位置

        Returns:
            连通区域中的所有位置列表
        """
        if not self.is_passable(start_pos):
            return []

        visited = set()
        area = []
        stack = [start_pos]

        while stack:
            pos = stack.pop()
            if pos in visited:
                continue

            visited.add(pos)
            area.append(pos)

            # 检查四个方向
            directions = [
                Position(0, -1),  # 上
                Position(0, 1),   # 下
                Position(-1, 0),  # 左
                Position(1, 0)    # 右
            ]

            for direction in directions:
                new_pos = pos + direction
                if (0 <= new_pos.x < self.width and
                    0 <= new_pos.y < self.height and
                    new_pos not in visited and
                    self.is_passable(new_pos)):
                    stack.append(new_pos)

        return area

    def has_monsters_in_area(self, area: List[Position]) -> bool:
        """
        检查指定区域内是否有存活的怪物

        Args:
            area: 区域位置列表

        Returns:
            True如果区域内有存活的怪物
        """
        area_set = set(area)  # 转换为集合提高查询效率

        for monster in self.monsters.values():
            if monster.is_alive() and monster.position in area_set:
                return True

        return False

    def get_3x3_area(self, center_pos: Position) -> List[Position]:
        """
        获取以指定位置为中心的3x3范围内的所有有效位置

        Args:
            center_pos: 中心位置

        Returns:
            3x3范围内所有有效的位置列表（考虑地图边界）
        """
        area = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                new_x = center_pos.x + dx
                new_y = center_pos.y + dy
                # 检查边界
                if 0 <= new_x < self.width and 0 <= new_y < self.height:
                    area.append(Position(new_x, new_y))
        return area

    def has_monsters_in_3x3_area(self, center_pos: Position) -> bool:
        """
        检查3x3范围内是否有存活的怪物

        Args:
            center_pos: 中心位置

        Returns:
            True如果3x3范围内有存活的怪物
        """
        area = self.get_3x3_area(center_pos)
        return self.has_monsters_in_area(area)

    def is_valid_placement_position(self, pos: Position) -> bool:
        """
        检查位置是否适合放置新实体（怪物或道具）

        Args:
            pos: 要检查的位置

        Returns:
            True如果位置可以放置，False如果已有实体
        """
        # 边界检查
        if not (0 <= pos.x < self.width and 0 <= pos.y < self.height):
            return False

        # 检查格子是否可通行
        if not self.is_passable(pos):
            return False

        # 检查是否已有怪物
        monster = self.get_monster_at(pos)
        if monster:
            return False

        # 检查是否已知道具
        item = self.get_item_at(pos)
        if item:
            return False

        # 检查是否是楼梯
        if self.stairs_pos and self.stairs_pos == pos:
            return False

        return True

    def debug_monster_threat_detection(self, target_pos: Position, context: str = ""):
        """
        详细的威胁检测调试方法

        Args:
            target_pos: 要检查的目标位置
            context: 调用时的上下文（拾取道具/上楼梯等）
        """
        print(f"\n=== 怪物威胁检测调试 {context} ===")
        print(f"目标位置: {target_pos}")
        print(f"地图边界: 0-14, 0-14")
        print(f"怪物总数: {len(self.monsters)}")

        if not (0 <= target_pos.x < self.width and 0 <= target_pos.y < self.height):
            print(f"❌ 目标位置超出地图范围!")
            return

        print(f"\n怪物详情:")
        monster_index = 1
        for monster_id, monster in self.monsters.items():
            distance = abs(monster.position.x - target_pos.x) + abs(monster.position.y - target_pos.y)
            status = "存活" if monster.is_alive() else "死亡"
            threat_status = "✅威胁" if (monster.is_alive() and distance <= 3) else "❌不威胁"

            print(f"  {monster_index}. {monster.name} (ID: {monster_id})")
            print(f"     位置: {monster.position}")
            print(f"     状态: {status} (HP: {monster.hp})")
            print(f"     距离目标: {distance}")
            print(f"     威胁状态: {threat_status}")
            if monster.is_alive() and distance <= 3:
                print(f"     🚫 这只怪物阻止了{context}!")
            monster_index += 1

        # 最终结论
        is_blocked = self.is_item_or_stairs_blocked_by_monster(target_pos)
        print(f"\n🔍 最终结论: {context} {'被阻止' if is_blocked else '可进行'}")
        print("=" * 50)

    def is_item_or_stairs_blocked_by_monster(self, target_pos: Position) -> bool:
        """
        检查目标位置（道具或楼梯）是否被怪物周围3格内限制

        Args:
            target_pos: 道具或楼梯的位置

        Returns:
            True如果被怪物限制（无法访问），False如果可以访问
        """
        # 边界检查：确保目标位置在地图范围内
        if not (0 <= target_pos.x < self.width and 0 <= target_pos.y < self.height):
            return False  # 超出范围的位置不限制

        for monster in self.monsters.values():
            if monster.is_alive():
                # 检查曼哈顿距离是否≤3
                distance = abs(monster.position.x - target_pos.x) + abs(monster.position.y - target_pos.y)
                if distance <= 3:
                    return True
        return False

    def get_threatening_monsters_for_position(self, target_pos: Position) -> list:
        """
        获取威胁指定位置的怪物列表（用于调试）

        Args:
            target_pos: 目标位置

        Returns:
            威胁该位置的怪物列表
        """
        threatening_monsters = []
        if not (0 <= target_pos.x < self.width and 0 <= target_pos.y < self.height):
            return threatening_monsters

        for monster in self.monsters.values():
            if monster.is_alive():
                distance = abs(monster.position.x - target_pos.x) + abs(monster.position.y - target_pos.y)
                if distance <= 3:
                    threatening_monsters.append({
                        'name': monster.name,
                        'position': monster.position,
                        'distance': distance
                    })
        return threatening_monsters

    def to_serializable_grid(self, player: 'Player' = None) -> List[List[str]]:
        """
        转换为可序列化的二维字符串数组，用于JSON传输

        Args:
            player: 玩家对象（可选），如果提供，会在玩家位置显示'@'

        Returns:
            二维字符串数组
        """
        result = []
        for x in range(self.width):
            row = []
            for y in range(self.height):
                # 如果这个位置是玩家，显示'@'
                if player and player.position.x == x and player.position.y == y:
                    row.append('@')
                else:
                    # 否则显示格子内容
                    cell = self.grid[x][y]
                    if cell.entity is not None:
                        row.append(cell.entity.symbol)
                    else:
                        row.append(cell.type.value)
            result.append(row)
        return result


# ==================== Boss定义 ====================

# 最终Boss：死亡骑士（第100层）
FINAL_BOSS = {
    "name": "死亡骑士",
    "hp": 5000,
    "atk": 800,
    "def": 200,
    "exp": 0,  # 通关，不给经验
    "gold": 9999,
    "symbol": "B"
}
