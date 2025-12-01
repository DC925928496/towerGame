import random
from typing import List, Optional, Dict

from game_model import (
    Floor, Room, Position, Cell, CellType,
    Monster, Item, FINAL_BOSS, Merchant, MerchantItem,
    WeaponAttribute, ATTRIBUTE_TYPES, RARITY_CONFIG
)

# 导入新的工具类和配置
from utils.position_utils import PositionUtils
from utils.game_utils import GameUtils
from config.game_config import config_manager, ITEM_CONFIGS


# ==================== 怪物名称库 ====================

MONSTER_NAMES = [
    "史莱姆", "哥布林", "骷髅兵", "僵尸", "蝙蝠",
    "史莱姆王", "兽人", "幽灵", "狼人", "石像鬼",
    "黑暗法师", "恶魔", "吸血鬼", "龙人", "熔岩怪"
]

MONSTER_PREFIXES = ["", "强化", "精英", "狂暴", "暗影", "诅咒"]


def find_nearest_valid_position(floor: Floor, target_pos: Position) -> Position:
    """
    找到距离目标位置最近的可用位置

    Args:
        floor: 楼层对象
        target_pos: 目标位置

    Returns:
        最近的可用位置
    """
    # 首先检查目标位置本身
    if (0 <= target_pos.x < floor.width and
        0 <= target_pos.y < floor.height and
        floor.grid[target_pos.x][target_pos.y].passable):

        has_entity = (floor.get_monster_at(target_pos) or
                     floor.get_item_at(target_pos))

        if not has_entity:
            return target_pos

    # 从目标位置开始，逐渐扩大搜索范围
    max_radius = max(floor.width, floor.height)
    for radius in range(1, max_radius):
        # 在指定半径内搜索可用位置
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) == radius or abs(dy) == radius:  # 只搜索边缘
                    candidate_pos = Position(
                        target_pos.x + dx,
                        target_pos.y + dy
                    )

                    # 检查边界和通行性
                    if (0 <= candidate_pos.x < floor.width and
                        0 <= candidate_pos.y < floor.height and
                        floor.grid[candidate_pos.x][candidate_pos.y].passable):

                        has_entity = (floor.get_monster_at(candidate_pos) or
                                     floor.get_item_at(candidate_pos))

                        if not has_entity:
                            return candidate_pos

    # 如果找不到，返回任意可用位置
    for x in range(floor.width):
        for y in range(floor.height):
            pos = Position(x, y)
            if floor.grid[pos.x][pos.y].passable:
                has_entity = (floor.get_monster_at(pos) or floor.get_item_at(pos))
                if not has_entity:
                    return pos

    # 如果还是找不到（极端情况），返回地图中心位置
    default_pos = Position(floor.width // 2, floor.height // 2)
    return default_pos


# ==================== 守卫系统工具函数 ====================

def get_item_weight(item_type: str) -> float:
    """从配置获取物品守卫权重"""
    config = config_manager.get_config()
    weight_map = {
        'weapon': config.WEAPON_WEIGHT,
        'armor': config.ARMOR_WEIGHT,
        'stairs': config.STAIR_WEIGHT,
        'potion': config.POTION_WEIGHT
    }
    return weight_map.get(item_type, 0.1)

def get_guard_radius(item_type: str) -> int:
    """从配置获取物品守卫半径"""
    config = config_manager.get_config()

    # 使用配置化的守卫半径，重要物品需要更大半径
    if item_type in ['weapon', 'armor']:
        return 3  # 武器和防具守卫半径3格
    elif item_type == 'stairs':
        return 2  # 楼梯守卫半径2格
    else:
        return 2  # 血瓶守卫半径2格

def calculate_guard_score(candidate_pos: Position, target_pos: Position, item_type: str) -> float:
    """计算候选位置作为守卫位置的评分"""
    distance = PositionUtils.manhattan_distance(candidate_pos, target_pos)

    # 获取物品权重
    base_weight = get_item_weight(item_type)

    # 距离评分（越近越好，但不要太近）
    if distance == 0:
        return 0  # 不要直接站在物品上
    elif distance <= 2:
        return base_weight * 1.5  # 近距离高评分
    elif distance <= get_guard_radius(item_type):
        return base_weight * (1.0 - (distance - 2) * 0.2)  # 距离增加评分递减
    else:
        return base_weight * 0.1  # 超出半径低评分

def is_valid_guard_position_relaxed(floor: Floor, pos: Position, existing_guards: List[Position], min_distance: int = 1) -> bool:
    """检查位置是否适合作为守卫位置（宽松版）"""
    # 检查边界
    if not (0 <= pos.x < floor.width and 0 <= pos.y < floor.height):
        return False

    # 检查是否可通行（允许楼梯位置，因为楼梯本身是可通行的）
    cell = floor.grid[pos.x][pos.y]
    if cell.type == CellType.WALL or not cell.passable:
        return False

    # 检查是否已有实体（怪物或道具）
    if cell.entity is not None:
        return False

    # 检查是否与现有守卫太近（使用指定的最小距离）
    for guard_pos in existing_guards:
        if PositionUtils.manhattan_distance(pos, guard_pos) < min_distance:
            return False

    return True

def is_valid_guard_position(floor: Floor, pos: Position, existing_guards: List[Position]) -> bool:
    """检查位置是否适合作为守卫位置"""
    # 检查边界
    if not (0 <= pos.x < floor.width and 0 <= pos.y < floor.height):
        return False

    # 检查是否可通行
    cell = floor.grid[pos.x][pos.y]
    if not cell.passable or cell.type == CellType.WALL:
        return False

    # 检查是否已有实体
    if cell.entity is not None:
        return False

    # 检查是否与现有守卫太近（避免重叠）
    for guard_pos in existing_guards:
        if PositionUtils.manhattan_distance(pos, guard_pos) <= 1:
            return False

    return True

# ==================== 武器随机属性生成 ====================

def generate_weapon_attributes(floor_level: int, rarity: str) -> List[WeaponAttribute]:
    """为武器生成随机属性列表"""
    if rarity not in RARITY_CONFIG:
        rarity = 'common'

    attr_count = RARITY_CONFIG[rarity]['attr_count']

    # 随机选择属性类型（不重复）
    available_types = list(ATTRIBUTE_TYPES.keys())
    selected_types = random.sample(available_types, min(attr_count, len(available_types)))

    attributes = []
    for attr_type in selected_types:
        attr_config = ATTRIBUTE_TYPES[attr_type]

        # 基于楼层和稀有度计算数值
        base_value = attr_config['base_value'] + floor_level * attr_config['scale']
        rarity_multiplier = RARITY_CONFIG[rarity]['multiplier']
        final_value = base_value * rarity_multiplier

        # 创建属性 - 处理特殊格式化字符串
        description = attr_config['description']
        if '{value*100}' in description:
            # 对于百分比格式，需要先计算乘积再格式化
            description = description.replace('{value*100}', f'{final_value*100:.1f}')
        else:
            description = description.format(value=final_value)

        attribute = WeaponAttribute(
            attribute_type=attr_type,
            value=final_value,
            description=description,
            level=0
        )
        attributes.append(attribute)

    return attributes

def generate_weapon_name(floor_level: int, rarity: str, attributes: List[WeaponAttribute]) -> str:
    """为武器生成动态名称"""
    # 获取稀有度前缀
    rarity_config = RARITY_CONFIG[rarity]
    prefix = random.choice(rarity_config['prefixes'])

    # 根据主要属性选择后缀
    if not attributes:
        base_name = "短剑"
    else:
        # 选择数值最高的属性作为武器特性
        main_attr = max(attributes, key=lambda a: a.value)
        attr_names = {
            'attack_boost': '力量',
            'damage_mult': '狂暴',
            'armor_pen': '穿透',
            'life_steal': '吸血',
            'gold_bonus': '财富',
            'critical_chance': '致命'
        }
        base_name = attr_names.get(main_attr.attribute_type, '神兵')

    return f"{prefix}{base_name}"

def generate_rarity() -> str:
    """随机生成稀有度"""
    # 使用加权随机选择
    weights = []
    rarities = []
    for rarity, config in RARITY_CONFIG.items():
        weights.append(config['probability'])
        rarities.append(rarity)

    return random.choices(rarities, weights=weights)[0]

# ==================== 生成函数 ====================

def generate_monster(floor_level: int, position: Position) -> Monster:
    """生成怪物，属性随层数指数增长"""
    # 基础属性随层数增长
    base_hp = 80 + floor_level * 20
    base_atk = 25 + floor_level * 5
    base_def = 12 + floor_level * 2
    base_exp = 20 + floor_level * 5
    base_gold = 10 + floor_level * 3

    # 添加随机因子（±20%）
    hp = int(base_hp * random.uniform(0.8, 1.2))
    atk = int(base_atk * random.uniform(0.8, 1.2))
    defense = int(base_def * random.uniform(0.8, 1.2))
    exp = int(base_exp * random.uniform(0.8, 1.2))
    gold = int(base_gold * random.uniform(0.8, 1.2))

    # 如果是最终Boss（第100层）
    if floor_level == 100:
        return Monster(
            monster_id="boss_death_knight",
            name=FINAL_BOSS["name"],
            hp=FINAL_BOSS["hp"],
            atk=FINAL_BOSS["atk"],
            defense=FINAL_BOSS["def"],
            exp=FINAL_BOSS["exp"],
            gold=FINAL_BOSS["gold"],
            position=position
        )

    # 随机名称
    name = random.choice(MONSTER_NAMES)
    prefix = random.choice(MONSTER_PREFIXES)
    if prefix:
        full_name = f"{prefix}{name}"
    else:
        full_name = name

    return Monster(
        monster_id=f"monster_{random.randint(1000, 9999)}",
        name=full_name,
        hp=hp,
        atk=atk,
        defense=defense,
        exp=exp,
        gold=gold,
        position=position
    )


def generate_guard_monster(floor_level: int, position: Position, guarded_item_type: str) -> Monster:
    """生成守卫怪物，属性根据守卫物品类型调整"""
    # 基础怪物生成
    monster = generate_monster(floor_level, position)

    # 根据守卫物品类型调整属性
    if guarded_item_type in ['weapon', 'armor']:
        # 守卫重要装备的怪物更强
        monster.name = f"守卫{monster.name}"
        monster.hp = int(monster.hp * 1.3)
        monster.atk = int(monster.atk * 1.2)
        monster.defense = int(monster.defense * 1.1)
        monster.exp = int(monster.exp * 1.5)
        monster.gold = int(monster.gold * 1.3)
    elif guarded_item_type == 'stairs':
        # 守卫楼梯的怪物
        monster.name = f"楼梯守卫{monster.name}"
        monster.hp = int(monster.hp * 1.2)
        monster.atk = int(monster.atk * 1.1)
        monster.exp = int(monster.exp * 1.3)

    return monster

def find_best_guard_position(floor: Floor, rooms: List[Room], target_item: Item,
                           existing_guards: List[Position]) -> Optional[Position]:
    """为指定物品找到最佳的守卫位置"""
    best_score = 0
    best_position = None

    radius = get_guard_radius(target_item.effect_type)

    # 在物品周围搜索最佳守卫位置
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            if dx == 0 and dy == 0:
                continue  # 跳过物品本身位置

            candidate_pos = Position(target_item.position.x + dx, target_item.position.y + dy)

            # 检查位置有效性（使用更宽松的条件）
            if not is_valid_guard_position_relaxed(floor, candidate_pos, existing_guards):
                continue

            # 计算守卫评分
            score = calculate_guard_score(candidate_pos, target_item.position, target_item.effect_type)

            if score > best_score:
                best_score = score
                best_position = candidate_pos

    # 如果找不到合适位置，尝试扩大搜索半径
    if best_position is None and radius < 5:
        extended_radius = min(radius + 2, 5)
        for dx in range(-extended_radius, extended_radius + 1):
            for dy in range(-extended_radius, extended_radius + 1):
                if dx == 0 and dy == 0:
                    continue

                candidate_pos = Position(target_item.position.x + dx, target_item.position.y + dy)

                # 使用更宽松的条件
                if not is_valid_guard_position_relaxed(floor, candidate_pos, existing_guards, min_distance=0):
                    continue

                score = calculate_guard_score(candidate_pos, target_item.position, target_item.effect_type)

                if score > best_score:
                    best_score = score
                    best_position = candidate_pos

    return best_position

def place_guard_monsters(floor: Floor, rooms: List[Room], key_items: List[Item]) -> List[Position]:
    """在关键物品附近战略性放置守卫怪物"""
    guard_positions = []

    # 按物品价值排序（武器/防具优先）
    sorted_items = sorted(key_items, key=lambda item: get_item_weight(item.effect_type), reverse=True)

    for item in sorted_items:
        best_guard_pos = find_best_guard_position(floor, rooms, item, guard_positions)
        if best_guard_pos:
            guard_positions.append(best_guard_pos)
            # 创建守卫怪物
            monster = generate_guard_monster(floor.level, best_guard_pos, item.effect_type)
            floor.monsters[monster.id] = monster
            floor.grid[best_guard_pos.x][best_guard_pos.y].entity = monster

    return guard_positions

def place_remaining_monsters(floor: Floor, rooms: List[Room], guard_positions: List[Position],
                           remaining_count: int):
    """放置剩余的随机怪物"""
    for _ in range(remaining_count):
        attempts = 0
        while attempts < 50:
            room = random.choice(rooms)
            pos = Position(
                random.randint(room.x + 1, room.x + room.width - 2),
                random.randint(room.y + 1, room.y + room.height - 2)
            )

            # 检查该位置是否为空地且不是守卫位置
            if (floor.grid[pos.x][pos.y].type == CellType.EMPTY and
                pos not in guard_positions and
                pos not in [floor.player_start_pos, floor.stairs_pos] and
                floor.is_valid_placement_position(pos)):  # 新增：检查是否与现有实体冲突

                monster = generate_monster(floor.level, pos)
                floor.monsters[monster.id] = monster
                floor.grid[pos.x][pos.y].entity = monster
                break

            attempts += 1

def place_strategic_item(floor: Floor, rooms: List[Room], key_items: List[Item]) -> Optional[Item]:
    """战略性地放置道具，优先放置高价值道具"""
    attempts = 0
    while attempts < 50:
        room = random.choice(rooms)
        pos = Position(
            random.randint(room.x + 1, room.x + room.width - 2),
            random.randint(room.y + 1, room.y + room.height - 2)
        )

        # 检查该位置是否为空地
        if (floor.grid[pos.x][pos.y].type == CellType.EMPTY and
            pos not in [floor.player_start_pos, floor.stairs_pos] and
            floor.is_valid_placement_position(pos)):  # 新增：检查是否与现有实体冲突

            # 生成道具
            item = generate_item(floor.level, pos)

            # 添加到地图
            floor.items[item.item_id] = item
            floor.grid[pos.x][pos.y] = Cell(CellType.EMPTY, passable=True, entity=item)

            return item

        attempts += 1

    return None

def generate_item(floor_level: int, position: Position) -> Item:
    """生成道具，属性随层数增长"""
    item_type = random.choices(
        ['potion', 'weapon', 'armor'],
        weights=[0.4, 0.3, 0.3]
    )[0]

    if item_type == 'potion':
        # 血瓶：回复量随层数增长
        effect_value = 100 + floor_level * 20
        name = f"血瓶"
        symbol = '+'
        return Item(
            symbol=symbol,
            name=name,
            effect_type=item_type,
            effect_value=effect_value,
            position=position
        )
    elif item_type == 'weapon':
        # 生成随机稀有度武器
        rarity = generate_rarity()
        attributes = generate_weapon_attributes(floor_level, rarity)
        weapon_name = generate_weapon_name(floor_level, rarity, attributes)
        attack_value = floor_level * 5

        return Item(
            symbol='↑',
            name=weapon_name,
            effect_type='weapon',
            effect_value=attack_value,
            position=position,
            rarity=rarity,
            attributes=attributes,
            base_name=weapon_name
        )
    else:  # armor
        # 防具：防御加成随层数增长（防具暂不支持随机属性）
        effect_value = floor_level * 3
        name = f"铠甲+{effect_value}"
        symbol = '◆'

        return Item(
            symbol=symbol,
            name=name,
            effect_type=item_type,
            effect_value=effect_value,
            position=position
        )


def connect_rooms(room1: Room, room2: Room, floor: Floor):
    """连接两个房间，用直线走廊"""
    # 从room1中心到room2中心
    x1, y1 = room1.center.x, room1.center.y
    x2, y2 = room2.center.x, room2.center.y

    # 优先水平后垂直（L型走廊）
    if random.random() < 0.5:
        # 先水平后垂直
        min_x, max_x = min(x1, x2), max(x1, x2)
        for x in range(min_x, max_x + 1):
            if floor.grid[x][y1].type == CellType.WALL:
                floor.grid[x][y1] = Cell(CellType.EMPTY, passable=True)

        min_y, max_y = min(y1, y2), max(y1, y2)
        for y in range(min_y, max_y + 1):
            if floor.grid[x2][y].type == CellType.WALL:
                floor.grid[x2][y] = Cell(CellType.EMPTY, passable=True)
    else:
        # 先垂直后水平
        min_y, max_y = min(y1, y2), max(y1, y2)
        for y in range(min_y, max_y + 1):
            if floor.grid[x1][y].type == CellType.WALL:
                floor.grid[x1][y] = Cell(CellType.EMPTY, passable=True)

        min_x, max_x = min(x1, x2), max(x1, x2)
        for x in range(min_x, max_x + 1):
            if floor.grid[x][y2].type == CellType.WALL:
                floor.grid[x][y2] = Cell(CellType.EMPTY, passable=True)


# ==================== 商人楼层生成 ====================

def generate_merchant(floor_level: int) -> Merchant:
    """生成商人和商品"""
    inventory = generate_merchant_inventory(floor_level)
    return Merchant(position=None, inventory=inventory)

def generate_merchant_inventory(floor_level: int) -> List[MerchantItem]:
    """生成商人库存"""
    inventory = []
    base_price = 10 + floor_level * 5  # 动态定价基础

    # 药水 (3-4个)
    potion_count = random.randint(3, 4)
    for i in range(potion_count):
        hp = 50 + floor_level * 20
        price = base_price * 2
        inventory.append(MerchantItem("血瓶", "potion", hp, price))

    # 武器 (2-3个)
    weapon_count = random.randint(2, 3)
    for i in range(weapon_count):
        atk = floor_level * 5 + 10
        price = base_price * 3
        inventory.append(MerchantItem("长剑", "weapon", atk, price))

    # 防具 (2-3个)
    armor_count = random.randint(2, 3)
    for i in range(armor_count):
        defense = floor_level * 3 + 5
        price = int(base_price * 2.5)
        inventory.append(MerchantItem("铠甲", "armor", defense, price))

    return inventory

def generate_merchant_floor(floor_level: int) -> Floor:
    """生成商人楼层：15×15空房间，商人在中央，楼梯在角落"""
    config = config_manager.get_config()
    width, height = config.GRID_SIZE, config.GRID_SIZE

    floor = Floor(floor_level, width, height)
    floor.is_merchant_floor = True

    # 15×15空房间，只有边界墙壁
    for y in range(height):
        for x in range(width):
            # 创建边界墙壁
            if y == 0 or y == height - 1 or x == 0 or x == width - 1:
                floor.grid[x][y] = Cell(CellType.WALL, passable=False)
            else:
                floor.grid[x][y] = Cell(CellType.EMPTY, passable=True)

    # 商人在中央 (7, 7)
    merchant_pos = Position(7, 7)
    merchant = generate_merchant(floor_level)
    merchant.position = merchant_pos
    floor.merchant = merchant
    floor.grid[7][7] = Cell(CellType.EMPTY, passable=True, entity=merchant)

    # 楼梯在角落 (1, 1)
    floor.stairs_pos = Position(1, 1)
    floor.grid[1][1] = Cell(CellType.STAIRS, passable=True)

    # 玩家起始位置在另一角 (13, 13)
    floor.player_start_pos = Position(13, 13)

    return floor


def generate_floor(level: int, prev_floor: Optional[Floor] = None, merchant_attempt_count: int = 0) -> Floor:
    """
    生成楼层（房间+走廊风格）

    Args:
        level: 楼层数（1-100）
        prev_floor: 上一层（用于获取玩家出生点）

    Returns:
        Floor对象
    """
    config = config_manager.get_config()

    # 商人楼层判断：前十层固定普通，第十层固定商人，之后累积概率
    if level < 10:
        # 前9层固定不触发
        pass  # 继续生成普通楼层
    elif level == 10:
        # 第10层固定触发商人楼层
        return generate_merchant_floor(level)
    elif level > 10 and level % 10 == 0 and level < 100:
        # 11层起，每10层累积概率机制
        # 计算累积概率：基础10% + 每次增加5%
        base_probability = 0.1  # 基础概率10%
        increment = 0.05  # 每次增加5%
        probability = min(base_probability + merchant_attempt_count * increment, 1.0)  # 最高100%

        if random.random() < probability:
            # 触发商人楼层，重置计数器
            return generate_merchant_floor(level)

    width, height = config.GRID_SIZE, config.GRID_SIZE
    floor = Floor(level, width, height)

    # 1. 创建房间数量从配置获取
    rooms: List[Room] = []
    room_count = random.randint(config.ROOM_COUNT_MIN, config.ROOM_COUNT_MAX)
    max_attempts = 100

    for _ in range(room_count):
        attempts = 0
        while attempts < max_attempts:
            # 随机房间大小从配置获取
            room_width = random.randint(config.ROOM_SIZE_MIN, config.ROOM_SIZE_MAX)
            room_height = random.randint(config.ROOM_SIZE_MIN, config.ROOM_SIZE_MAX)

            # 随机位置（留出边界1格）
            x = random.randint(1, width - room_width - 1)
            y = random.randint(1, height - room_height - 1)

            new_room = Room(x, y, room_width, room_height)

            # 检查是否与其他房间重叠
            overlap = any(new_room.intersects(room) for room in rooms)

            if not overlap:
                rooms.append(new_room)
                break

            attempts += 1

    # 2. 绘制房间
    for room in rooms:
        for i in range(room.x, room.x + room.width):
            for j in range(room.y, room.y + room.height):
                floor.grid[i][j] = Cell(CellType.EMPTY, passable=True)

    # 3. 用走廊连接房间
    if len(rooms) > 1:
        for i in range(len(rooms) - 1):
            connect_rooms(rooms[i], rooms[i + 1], floor)

    # 4. 放置玩家、楼梯、怪物、道具
    if rooms:
        # 玩家出生点
        if prev_floor and prev_floor.player_start_pos:
            # 从上层继续：出生在上层的楼梯位置
            potential_start_pos = prev_floor.stairs_pos

            # 验证楼梯位置是否可用，如果不可用则寻找最近可用位置
            if (0 <= potential_start_pos.x < floor.width and
                0 <= potential_start_pos.y < floor.height and
                floor.grid[potential_start_pos.x][potential_start_pos.y].passable):

                # 检查是否已有实体
                has_entity = (floor.get_monster_at(potential_start_pos) or
                             floor.get_item_at(potential_start_pos))

                if not has_entity:
                    floor.player_start_pos = potential_start_pos
                else:
                    # 有实体时寻找最近可用位置
                    floor.player_start_pos = find_nearest_valid_position(floor, potential_start_pos)
            else:
                # 楼梯位置不可通达时寻找最近可用位置
                floor.player_start_pos = find_nearest_valid_position(floor, potential_start_pos)
        else:
            # 第一层：选取第一个房间中心并验证可用性
            potential_center = rooms[0].center
            if (0 <= potential_center.x < floor.width and
                0 <= potential_center.y < floor.height and
                floor.grid[potential_center.x][potential_center.y].passable):
                floor.player_start_pos = potential_center
            else:
                floor.player_start_pos = find_nearest_valid_position(floor, potential_center)

        # 楼梯位置（不能与玩家同房间）
        if level < 100:
            stair_rooms = [room for room in rooms if room.center != floor.player_start_pos]
            if stair_rooms:
                floor.stairs_pos = random.choice(stair_rooms).center
            else:
                floor.stairs_pos = rooms[-1].center

            floor.grid[floor.stairs_pos.x][floor.stairs_pos.y] = Cell(
                CellType.STAIRS, passable=True
            )

        # === 新的战略性放置系统 ===

        # 1. 识别关键物品位置（武器、防具、楼梯）
        key_items = []

        # 楼梯被视为关键物品
        if level < 100:
            stairs_item = Item(
                symbol='>', name='楼梯', effect_type='stairs',
                effect_value=0, position=floor.stairs_pos, item_id=f'stairs_{level}'
            )
            key_items.append(stairs_item)

        # 2. 优先放置高价值道具（武器、防具）
        if level < 100:
            high_value_item_count = 1 + level // 10  # 每10层+1个高价值道具
            high_value_items = []

            # 尝试放置武器和防具
            for _ in range(high_value_item_count):
                # 优先放置武器和防具
                weapon_armor_weights = [0.0, 0.5, 0.5]  # 血瓶0%，武器50%，防具50%
                item_type = random.choices(['potion', 'weapon', 'armor'], weights=weapon_armor_weights)[0]

                # 为武器和防具寻找合适位置
                if item_type in ['weapon', 'armor']:
                    item = place_strategic_item(floor, rooms, key_items)
                    if item and item.effect_type in ['weapon', 'armor']:
                        key_items.append(item)
                        high_value_items.append(item)

        # 3. 在关键物品附近战略性放置守卫怪物
        if key_items:
            guard_positions = place_guard_monsters(floor, rooms, key_items)
            # 计算还需要放置的随机怪物数量
            base_monster_count = 3 + level // 5
            guard_monster_count = len(guard_positions)
            remaining_monster_count = max(0, base_monster_count - guard_monster_count)
        else:
            guard_positions = []
            remaining_monster_count = 3 + level // 5

        # 4. 放置剩余的随机怪物（确保总数达标）
        if level < 100:
            place_remaining_monsters(floor, rooms, guard_positions, remaining_monster_count)

        # 5. 放置剩余的低价值道具（血瓶）
        if level < 100:
            # 计算还需要放置的血瓶数量
            total_item_count = 2 + level // 8
            high_value_count = len([item for item in key_items if item.effect_type in ['weapon', 'armor']])
            remaining_potion_count = max(0, total_item_count - high_value_count)

            for _ in range(remaining_potion_count):
                item = place_strategic_item(floor, rooms, key_items)
                if item and item.effect_type == 'potion':
                    # 为血瓶也尝试放置守卫（可选）
                    if random.random() < 0.5:  # 50%概率为血瓶放置守卫
                        key_items.append(item)

    return floor
