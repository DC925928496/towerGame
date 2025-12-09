import random
from typing import List, Optional, Dict

from game_model import (
    Floor, Room, Position, Cell, CellType,
    Monster, Item, FINAL_BOSS, Merchant, MerchantItem,
    WeaponAttribute, ArmorAttribute, ATTRIBUTE_TYPES, ARMOR_ATTRIBUTE_TYPES, RARITY_CONFIG
)

# 导入新的工具类和配置
from utils.position_utils import PositionUtils
from utils.game_utils import GameUtils
from config.game_config import config_manager


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

        # 基于楼层和稀有度计算数值，先计算浮点值，再按展示需求处理
        base_value = attr_config['base_value'] + floor_level * attr_config['scale']
        rarity_multiplier = RARITY_CONFIG[rarity]['multiplier']
        final_value = base_value * rarity_multiplier

        # 创建属性 - 处理特殊格式化字符串
        description = attr_config['description']
        if '{value*100}' in description:
            # 百分比类词条：使用一位小数展示百分比
            description = description.replace('{value*100}', f'{final_value*100:.1f}')
        else:
            # 非百分比词条：按整数四舍五入展示，避免出现长小数
            value_str = str(int(round(final_value)))
            description = description.format(value=value_str)

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
            'critical_chance': '致命',
            'combo_chance': '连击',
            'kill_heal': '嗜血',
            'exp_bonus': '成长',
            'thorn_damage': '荆棘',
            'damage_reduction': '坚韧',
            'percent_damage': '破甲',
            'floor_bonus': '传承',
            'lucky_hit': '幸运',
            'berserk_mode': '怒火'
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

def generate_armor_attributes(floor_level: int, rarity: str) -> List[ArmorAttribute]:
    """为防具生成随机属性列表"""
    if rarity not in RARITY_CONFIG:
        rarity = 'common'

    attr_count = RARITY_CONFIG[rarity]['attr_count']

    # 按权重选择属性类型（不重复）
    available_types = list(ARMOR_ATTRIBUTE_TYPES.keys())
    selected_types = []

    for _ in range(min(attr_count, len(available_types))):
        weights = [ARMOR_ATTRIBUTE_TYPES[attr]['weight'] for attr in available_types]
        selected = random.choices(available_types, weights=weights)[0]
        selected_types.append(selected)
        available_types.remove(selected)

    attributes = []
    for attr_type in selected_types:
        attr_config = ARMOR_ATTRIBUTE_TYPES[attr_type]

        # 基于楼层和稀有度计算数值，先计算浮点值，再按展示需求处理
        base_value = attr_config['base_value'] + floor_level * attr_config['scale']
        rarity_multiplier = RARITY_CONFIG[rarity]['multiplier']
        final_value = base_value * rarity_multiplier

        # 创建属性 - 处理特殊格式化字符串
        description = attr_config['description']
        if '{value*100}' in description:
            # 百分比类词条：使用一位小数展示百分比
            description = description.replace('{value*100}', f'{final_value*100:.1f}')
        else:
            # 非百分比词条：按整数四舍五入展示，避免出现长小数
            value_str = str(int(round(final_value)))
            description = description.format(value=value_str)

        attribute = ArmorAttribute(
            attribute_type=attr_type,
            value=final_value,
            description=description,
            level=0
        )
        attributes.append(attribute)

    return attributes

def generate_armor_name(floor_level: int, rarity: str, attributes: List[ArmorAttribute]) -> str:
    """为防具生成动态名称"""
    # 获取稀有度前缀
    rarity_config = RARITY_CONFIG[rarity]
    prefix = random.choice(rarity_config['prefixes'])

    # 根据主要属性选择后缀
    if not attributes:
        base_name = "布甲"
    else:
        # 选择数值最高的属性作为防具特性
        main_attr = max(attributes, key=lambda a: a.value)
        attr_names = {
            'defense_boost': '守护',
            'damage_reduction': '坚韧',
            'thorn_reflect': '荆棘',
            'block_chance': '格挡',
            'dodge_chance': '闪避',
            'hp_boost': '生命',
            'floor_heal': '恢复',
            'kill_heal': '嗜血',
            'potion_boost': '强化'
        }
        base_name = attr_names.get(main_attr.attribute_type, '护甲')

    armor_types = ['铠甲', '胸甲', '护甲', '战甲', '重甲', '轻甲']
    armor_type = random.choice(armor_types)

    return f"{prefix}{base_name}{armor_type}"

# ==================== 生成函数 ====================

def generate_monster(floor_level: int, position: Position) -> Monster:
    """生成怪物，属性随层数指数增长"""
    config = config_manager.get_config()

    base_hp = config.MONSTER_BASE_HP + floor_level * config.MONSTER_HP_PER_FLOOR
    base_atk = config.MONSTER_BASE_ATK + floor_level * config.MONSTER_ATK_PER_FLOOR
    base_def = config.MONSTER_BASE_DEF + floor_level * config.MONSTER_DEF_PER_FLOOR
    base_exp = config.MONSTER_BASE_EXP + floor_level * config.MONSTER_EXP_PER_FLOOR
    base_gold = config.MONSTER_BASE_GOLD + floor_level * config.MONSTER_GOLD_PER_FLOOR

    hp = int(base_hp * random.uniform(1 - config.MONSTER_HP_VARIANCE, 1 + config.MONSTER_HP_VARIANCE))
    atk = int(base_atk * random.uniform(1 - config.MONSTER_ATK_VARIANCE, 1 + config.MONSTER_ATK_VARIANCE))
    defense = int(base_def * random.uniform(1 - config.MONSTER_DEF_VARIANCE, 1 + config.MONSTER_DEF_VARIANCE))
    exp = int(base_exp)
    gold = int(base_gold * random.uniform(1 - config.MONSTER_GOLD_VARIANCE, 1 + config.MONSTER_GOLD_VARIANCE))

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

def place_strategic_item(floor: Floor, rooms: List[Room], key_items: List[Item], item_type: Optional[str] = None) -> Optional[Item]:
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

            item = generate_item(floor.level, pos, forced_type=item_type)

            # 添加到地图
            floor.items[item.item_id] = item
            floor.grid[pos.x][pos.y] = Cell(CellType.EMPTY, passable=True, entity=item)

            return item

        attempts += 1

    return None

def generate_item(floor_level: int, position: Position, forced_type: Optional[str] = None) -> Item:
    """生成道具，属性随层数增长"""
    config = config_manager.get_config()
    item_weights = config.ITEM_WEIGHTS

    if forced_type:
        item_type = forced_type
    else:
        item_types = list(item_weights.keys())
        weights = [item_weights[it] for it in item_types]
        item_type = random.choices(item_types, weights=weights)[0]

    if item_type == 'potion':
        # 使用档位+百分比回血的药瓶系统
        # 基础权重从配置读取，并根据楼层轻微偏向中/大药瓶
        base_weights = getattr(config, 'POTION_TYPE_WEIGHTS', None) or {
            'small': 0.5,
            'medium': 0.35,
            'large': 0.15
        }

        small_w = base_weights.get('small', 0.5)
        medium_w = base_weights.get('medium', 0.35)
        large_w = base_weights.get('large', 0.15)

        # 楼层越高，中/大药瓶权重越高，掉落机制更加友好
        if 20 <= floor_level < 50:
            small_w *= 0.7
            medium_w *= 1.2
            large_w *= 1.4
        elif floor_level >= 50:
            small_w *= 0.4
            medium_w *= 1.3
            large_w *= 1.8

        weight_sum = small_w + medium_w + large_w
        if weight_sum <= 0:
            small_w, medium_w, large_w = 0.5, 0.35, 0.15

        potion_types = ['small', 'medium', 'large']
        potion_weights = [small_w, medium_w, large_w]
        potion_type = random.choices(potion_types, weights=potion_weights)[0]

        if potion_type == 'medium':
            potion_name = config.POTION_MEDIUM_NAME
            heal_rate = config.POTION_MEDIUM_HEAL_RATE
        elif potion_type == 'large':
            potion_name = config.POTION_LARGE_NAME
            heal_rate = config.POTION_LARGE_HEAL_RATE
        else:
            potion_name = config.POTION_SMALL_NAME
            heal_rate = config.POTION_SMALL_HEAL_RATE

        # effect_value 使用百分比数值，便于前端与商人界面展示
        effect_value = int(heal_rate * 100)
        symbol = '+'
        return Item(
            symbol=symbol,
            name=potion_name,
            effect_type=item_type,
            effect_value=effect_value,
            position=position
        )
    elif item_type == 'weapon':
        rarity = generate_rarity()
        attributes = generate_weapon_attributes(floor_level, rarity)
        weapon_name = generate_weapon_name(floor_level, rarity, attributes)
        attack_value = config.WEAPON_BASE_ATK + floor_level * config.WEAPON_ATK_PER_FLOOR

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
        rarity = generate_rarity()
        armor_attributes = generate_armor_attributes(floor_level, rarity)
        armor_name = generate_armor_name(floor_level, rarity, armor_attributes)
        effect_value = config.ARMOR_BASE_DEF + floor_level * config.ARMOR_DEF_PER_FLOOR
        symbol = '◆'

        return Item(
            symbol=symbol,
            name=armor_name,
            effect_type=item_type,
            effect_value=effect_value,
            position=position,
            rarity=rarity,
            armor_attributes=armor_attributes,
            base_name=armor_name
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


def carve_corridor_between_positions(start: Position, end: Position, floor: Floor):
    """
    在玩家出生点与楼梯之间补一条简单走廊，确保连通性
    使用与 connect_rooms 相同的L型挖掘策略，避免破坏已有通路
    """
    if not start or not end:
        return

    x1, y1 = start.x, start.y
    x2, y2 = end.x, end.y

    # 先水平后垂直
    min_x, max_x = min(x1, x2), max(x1, x2)
    for x in range(min_x, max_x + 1):
        cell = floor.grid[x][y1]
        if cell.type == CellType.WALL:
            floor.grid[x][y1] = Cell(CellType.EMPTY, passable=True)

    min_y, max_y = min(y1, y2), max(y1, y2)
    for y in range(min_y, max_y + 1):
        cell = floor.grid[x2][y]
        if cell.type == CellType.WALL:
            floor.grid[x2][y] = Cell(CellType.EMPTY, passable=True)

# ==================== 商人楼层生成 ====================

def generate_merchant(floor_level: int) -> Merchant:
    """生成商人和商品"""
    inventory = generate_merchant_inventory(floor_level)
    return Merchant(position=None, inventory=inventory)

def generate_merchant_inventory(floor_level: int) -> List[MerchantItem]:
    """生成商人库存"""
    config = config_manager.get_config()
    inventory: List[MerchantItem] = []
    base_price = config.MERCHANT_BASE_PRICE + floor_level * config.MERCHANT_PRICE_PER_FLOOR

    # 药瓶 (3-4个)：与野外掉落共用档位/百分比配置
    potion_count = random.randint(*config.MERCHANT_POTION_RANGE)
    medium_percent = int(getattr(config, 'POTION_MEDIUM_HEAL_RATE', 0.5) * 100) or 50
    for i in range(potion_count):
        potion_item = generate_item(floor_level, Position(0, 0), forced_type='potion')
        rate_percent = potion_item.effect_value or medium_percent
        price_factor = rate_percent / medium_percent
        price = int(base_price * config.MERCHANT_POTION_PRICE_MULTIPLIER * price_factor)
        inventory.append(MerchantItem(
            potion_item.name,
            "potion",
            potion_item.effect_value,
            price
        ))

    # 武器 (2-3个)
    weapon_count = random.randint(*config.MERCHANT_WEAPON_RANGE)
    for i in range(weapon_count):
        weapon_item = generate_item(floor_level, Position(0, 0), forced_type='weapon')
        price = int(base_price * config.MERCHANT_WEAPON_PRICE_MULTIPLIER)
        inventory.append(MerchantItem(
            weapon_item.name,
            "weapon",
            weapon_item.effect_value,
            price,
            rarity=weapon_item.rarity,
            attributes=weapon_item.attributes.copy(),
            base_name=weapon_item.base_name
        ))

    # 防具 (2-3个)
    armor_count = random.randint(*config.MERCHANT_ARMOR_RANGE)
    for i in range(armor_count):
        armor_item = generate_item(floor_level, Position(0, 0), forced_type='armor')
        price = int(base_price * config.MERCHANT_ARMOR_PRICE_MULTIPLIER)
        inventory.append(MerchantItem(
            armor_item.name,
            "armor",
            armor_item.effect_value,
            price,
            rarity=armor_item.rarity,
            attributes=armor_item.armor_attributes.copy(),
            base_name=armor_item.base_name
        ))

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

    merchant_first_floor = config.MERCHANT_FIRST_FLOOR
    if level == merchant_first_floor:
        return generate_merchant_floor(level)
    elif merchant_first_floor < level < config.MAX_FLOORS:
        floors_since_last = merchant_attempt_count
        if floors_since_last >= config.MERCHANT_FORCE_INTERVAL:
            return generate_merchant_floor(level)

        probability = min(
            1.0,
            config.MERCHANT_BASE_CHANCE + floors_since_last * config.MERCHANT_CHANCE_INCREMENT
        )
        if floors_since_last > 0 and random.random() < probability:
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

            # 初步确保出生点与楼梯连通（此时尚未放置怪物/道具）
            if floor.player_start_pos:
                connected_area = floor.get_connected_area(floor.player_start_pos)
                if floor.stairs_pos not in connected_area:
                    carve_corridor_between_positions(floor.player_start_pos, floor.stairs_pos, floor)

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
        high_value_items: List[Item] = []
        if level < 100:
            config = config_manager.get_config()
            high_value_item_count = 0

            # 楼层保底掉落：首层与固定间隔一定提供装备
            if level == 1 or (config.HIGH_VALUE_ITEM_INTERVAL and level % config.HIGH_VALUE_ITEM_INTERVAL == 0):
                high_value_item_count += 1

            # 其余楼层按概率掉落，控制装备刷新频率
            if random.random() < config.HIGH_VALUE_ITEM_BASE_CHANCE:
                high_value_item_count += 1

            high_value_item_count = min(high_value_item_count, config.HIGH_VALUE_ITEM_MAX)

            # 一层最多生成 1 把武器和 1 件防具，避免同一层出现多把武器或多件防具
            weapon_spawned = False
            armor_spawned = False

            for _ in range(high_value_item_count):
                available_types = []
                if not weapon_spawned:
                    available_types.append('weapon')
                if not armor_spawned:
                    available_types.append('armor')

                # 已经同时有武器和防具时，不再额外生成高价值装备
                if not available_types:
                    break

                item_type = random.choice(available_types)
                item = place_strategic_item(floor, rooms, key_items, item_type=item_type)
                if item:
                    key_items.append(item)
                    high_value_items.append(item)
                    if item_type == 'weapon':
                        weapon_spawned = True
                    elif item_type == 'armor':
                        armor_spawned = True

        # 3. 在关键物品附近战略性放置守卫怪物
        if key_items:
            guard_positions = place_guard_monsters(floor, rooms, key_items)
            config = config_manager.get_config()
            base_monster_count = config.MONSTER_COUNT_BASE + level // max(1, config.MONSTER_COUNT_DIVISOR)
            guard_monster_count = len(guard_positions)
            remaining_monster_count = max(0, base_monster_count - guard_monster_count)
        else:
            guard_positions = []
            config = config_manager.get_config()
            remaining_monster_count = config.MONSTER_COUNT_BASE + level // max(1, config.MONSTER_COUNT_DIVISOR)

        # 4. 放置剩余的随机怪物（确保总数达标）
        if level < 100:
            place_remaining_monsters(floor, rooms, guard_positions, remaining_monster_count)

        # 5. 放置剩余的低价值道具（血瓶）
        if level < 100:
            total_item_count = 2 + level // 8
            high_value_count = len(high_value_items)
            remaining_potion_count = max(0, total_item_count - high_value_count)

            for _ in range(remaining_potion_count):
                place_strategic_item(floor, rooms, key_items, item_type='potion')

    return floor
