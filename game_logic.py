from typing import List, Optional, Dict, Any
import random
from game_model import Player, Monster, Floor, Position, CellType, Item, Cell, MerchantItem

# 导入新的工具类和配置
from utils.position_utils import PositionUtils
from utils.game_utils import GameUtils
from config.game_config import config_manager




def calculate_combo_damage(base_damage: int, combo_chance: float) -> List[Dict[str, Any]]:
    """
    计算连击伤害

    Args:
        base_damage: 基础伤害
        combo_chance: 连击概率

    Returns:
        连击伤害列表，每次连击的伤害信息
    """
    combo_attacks = []

    # 第一次连击：50%概率，25%伤害
    if random.random() < combo_chance:
        first_hit = int(base_damage * 0.25)
        combo_attacks.append({
            'damage': first_hit,
            'multiplier': 0.25,
            'hit_type': '第一次连击'
        })

        # 第二次连击：25%概率，50%伤害（基于基础伤害）
        if random.random() < 0.25:
            second_hit = int(base_damage * 0.50)
            combo_attacks.append({
                'damage': second_hit,
                'multiplier': 0.50,
                'hit_type': '第二次连击'
            })

            # 第三次连击：5%概率，75%伤害（基于基础伤害）
            if random.random() < 0.05:
                third_hit = int(base_damage * 0.75)
                combo_attacks.append({
                    'damage': third_hit,
                    'multiplier': 0.75,
                    'hit_type': '第三次连击'
                })

    return combo_attacks


def calculate_damage_with_attributes(atk: int, defense: int, player_attributes: List,
                                   critical_chance: float = 0.05, monster_max_hp: int = None) -> Dict[str, Any]:
    """
    考虑武器随机属性的伤害计算

    Args:
        atk: 基础攻击力
        defense: 防御力
        player_attributes: 玩家武器属性列表
        critical_chance: 暴击率
        monster_max_hp: 怪物最大生命值（用于百分比伤害计算）

    Returns:
        伤害计算结果字典，包含：
        - damage: 最终伤害
        - life_steal: 吸血量
        - is_critical: 是否暴击
        - is_lucky_hit: 是否幸运一击
        - combo_attacks: 连击伤害列表
        - percent_damage: 百分比伤害
        - damage_breakdown: 伤害构成详情
    """
    config = config_manager.get_config()

    # 计算基础伤害（应用无视防御）
    armor_pen = sum(attr.get_enhanced_value() for attr in player_attributes
                   if attr.attribute_type == 'armor_pen')
    effective_defense = max(0, defense - armor_pen)
    base_damage = max(config.MIN_DAMAGE, atk - effective_defense)

    # 应用攻击力加成
    attack_boost = sum(attr.get_enhanced_value() for attr in player_attributes
                     if attr.attribute_type == 'attack_boost')
    base_damage += attack_boost

    # 计算暴击
    is_critical = random.random() < critical_chance
    crit_multiplier = config.CRITICAL_HIT_MULTIPLIER if is_critical else 1.0

    # 应用伤害倍率
    damage_mult = 1.0
    damage_mult += sum(attr.get_enhanced_value() for attr in player_attributes
                       if attr.attribute_type == 'damage_mult')

    # 计算最终伤害
    final_damage = int(base_damage * damage_mult * crit_multiplier)

    # 计算幸运一击
    lucky_hit_chance = sum(attr.get_enhanced_value() for attr in player_attributes
                           if attr.attribute_type == 'lucky_hit')
    is_lucky_hit = random.random() < lucky_hit_chance
    if is_lucky_hit:
        final_damage *= 3  # 幸运一击造成3倍伤害

    # 计算百分比伤害
    percent_damage = 0
    if monster_max_hp:
        percent_rate = sum(attr.get_enhanced_value() for attr in player_attributes
                           if attr.attribute_type == 'percent_damage')
        if percent_rate > 0:
            percent_damage = int(monster_max_hp * percent_rate)
            # 对Boss的最大百分比伤害限制为5%
            if monster_max_hp > 1000:  # 假设Boss血量超过1000
                percent_damage = min(percent_damage, int(monster_max_hp * 0.05))

    # 计算连击
    combo_chance = sum(attr.get_enhanced_value() for attr in player_attributes
                      if attr.attribute_type == 'combo_chance')
    combo_attacks = calculate_combo_damage(final_damage, combo_chance)

    # 计算吸血量（包括连击吸血）
    life_steal = 0
    life_steal_rate = sum(attr.get_enhanced_value() for attr in player_attributes
                          if attr.attribute_type == 'life_steal')
    if life_steal_rate > 0:
        # 主攻击吸血
        life_steal = int(final_damage * life_steal_rate)
        # 连击吸血
        for combo in combo_attacks:
            life_steal += int(combo['damage'] * life_steal_rate)

    # 计算总伤害（主攻击 + 连击 + 百分比伤害）
    total_damage = final_damage + sum(combo['damage'] for combo in combo_attacks) + percent_damage

    # 伤害构成详情（用于调试和显示）
    damage_breakdown = {
        'base_atk': atk,
        'base_defense': defense,
        'armor_pen': armor_pen,
        'effective_defense': effective_defense,
        'attack_boost': attack_boost,
        'base_damage': base_damage,
        'damage_mult': damage_mult,
        'is_critical': is_critical,
        'crit_multiplier': crit_multiplier,
        'is_lucky_hit': is_lucky_hit,
        'final_damage': final_damage,
        'percent_damage': percent_damage,
        'combo_chance': combo_chance,
        'combo_count': len(combo_attacks),
        'combo_damage': sum(combo['damage'] for combo in combo_attacks),
        'total_damage': total_damage
    }

    return {
        'damage': final_damage,
        'total_damage': total_damage,
        'percent_damage': percent_damage,
        'combo_attacks': combo_attacks,
        'life_steal': life_steal,
        'is_critical': is_critical,
        'is_lucky_hit': is_lucky_hit,
        'damage_breakdown': damage_breakdown
    }


def calculate_damage(atk: int, defense: int) -> int:
    """
    计算伤害 - 使用配置化的最小伤害值
    伤害 = max(最小伤害, 攻击方.attack - 防御方.defense)

    Args:
        atk: 攻击力
        defense: 防御力

    Returns:
        造成的伤害值
    """
    config = config_manager.get_config()
    return max(config.MIN_DAMAGE, atk - defense)

def calculate_damage_with_armor_defense(base_damage: int, player: Player) -> tuple[int, list]:
    """
    计算包含防具词条的防御效果

    Args:
        base_damage: 基础伤害值
        player: 玩家对象

    Returns:
        (最终伤害值, 防具效果日志列表)
    """
    final_damage = base_damage
    logs = []

    # 伤害减免（乘法计算）
    reduction_rate = player.get_armor_attribute_value('damage_reduction')
    if reduction_rate > 0:
        old_damage = final_damage
        final_damage = int(final_damage * (1.0 - reduction_rate))
        reduction_amount = old_damage - final_damage
        logs.append(f"✨防具伤害减免！减少了{reduction_amount}点伤害")

    # 格挡（概率触发，减少60%伤害）
    block_chance = player.get_armor_attribute_value('block_chance')
    if block_chance > 0 and random.random() < block_chance:
        old_damage = final_damage
        final_damage = int(final_damage * 0.4)  # 格挡减少60%伤害
        block_reduction = old_damage - final_damage
        logs.append(f"🛡️格挡成功！减少了{block_reduction}点伤害")

    # 闪避（概率触发，完全避免）
    dodge_chance = player.get_armor_attribute_value('dodge_chance')
    if dodge_chance > 0 and random.random() < dodge_chance:
        final_damage = 0
        logs.append("💨闪避成功！完全避免伤害")

    # 确保最小伤害
    config = config_manager.get_config()
    final_damage = max(0, final_damage)  # 闪避时可以为0

    return final_damage, logs


def player_attack(player: Player, monster: Monster, floor: Floor) -> Dict[str, Any]:
    """
    玩家攻击怪物

    Args:
        player: 玩家对象
        monster: 怪物对象
        floor: 当前楼层

    Returns:
        战斗结果字典，包含：
        - success: 是否成功
        - player_damage: 玩家造成的伤害
        - monster_damage: 怪物造成的伤害（如果怪物存活）
        - monster_dead: 怪物是否死亡
        - exp_gained: 获得的经验值
        - gold_gained: 获得的金币
        - logs: 战斗日志列表
        - level_up_logs: 升级日志（如果有）
    """
    result = {
        'success': True,
        'player_damage': 0,
        'monster_damage': 0,
        'monster_dead': False,
        'exp_gained': 0,
        'gold_gained': 0,
        'logs': [],
        'level_up_logs': []
    }

    # 玩家攻击 - 使用新的武器属性系统
    attack_result = calculate_damage_with_attributes(
        player.total_atk(floor.level if floor else 1),
        monster.defense,
        player.weapon_attributes,
        player.get_critical_chance(),
        monster.hp + (monster.hp * 0.1) if monster.hp < monster.max_hp else monster.max_hp  # 估算最大生命值
    )

    # 应用主攻击伤害
    actual_damage = monster.take_damage(attack_result['damage'])
    result['player_damage'] = actual_damage

    # 伤害日志
    damage_desc = f"你对{monster.name}造成了{actual_damage}点伤害！"
    if attack_result['is_lucky_hit']:
        damage_desc = f"🍀幸运一击！{damage_desc}"
    elif attack_result['is_critical']:
        damage_desc = f"💥暴击！{damage_desc}"
    result['logs'].append(damage_desc)

    # 应用百分比伤害
    if attack_result.get('percent_damage', 0) > 0:
        percent_damage = monster.take_damage(attack_result['percent_damage'])
        result['player_damage'] += percent_damage
        result['logs'].append(f"🔸百分比伤害造成了{percent_damage}点伤害！")

    # 应用连击伤害（怪物不会反击连击）
    combo_total_damage = 0
    for i, combo in enumerate(attack_result['combo_attacks'], 1):
        combo_damage = monster.take_damage(combo['damage'])
        combo_total_damage += combo_damage
        result['logs'].append(f"⚡连击{i}！{combo['hit_type']}造成了{combo_damage}点伤害！")

    # 更新总伤害
    if combo_total_damage > 0:
        result['player_damage'] += combo_total_damage
        result['logs'].append(f"连击总计：{combo_total_damage}点额外伤害")

    # 吸血处理
    if attack_result['life_steal'] > 0:
        heal_amount = player.heal(attack_result['life_steal'])
        result['logs'].append(f"💈吸血效果恢复了{heal_amount}点生命值！")

    if not monster.is_alive():
        # 怪物死亡
        result['monster_dead'] = True

        result['logs'].append(f"你击败了{monster.name}！")

        # 应用经验加成
        exp_bonus_rate = player.get_exp_bonus_rate()
        bonus_exp = int(monster.exp * exp_bonus_rate)
        total_exp = monster.exp + bonus_exp

        result['exp_gained'] = total_exp
        if bonus_exp > 0:
            result['logs'].append(f"获得了{monster.exp}点经验值（成长词条额外加成{bonus_exp}点）！")
        else:
            result['logs'].append(f"获得了{monster.exp}点经验值！")

        # 获得经验值和升级
        level_up_logs = player.gain_exp(total_exp)
        result['level_up_logs'] = level_up_logs
        result['logs'].extend(level_up_logs)

        # 获得金币（应用金币加成）
        gold_bonus_rate = player.get_gold_bonus_rate()
        bonus_gold = int(monster.gold * gold_bonus_rate)
        total_gold = monster.gold + bonus_gold

        if bonus_gold > 0:
            result['logs'].append(f"获得了{monster.gold}金币（财富词条额外加成{bonus_gold}金币）！")
        else:
            result['logs'].append(f"获得了{monster.gold}金币！")

        result['gold_gained'] = total_gold
        player.gold += total_gold

        # 应用击杀回血
        kill_heal_amount = player.get_kill_heal_amount()
        if kill_heal_amount > 0:
            heal_amount = player.heal(kill_heal_amount)
            if heal_amount > 0:
                result['logs'].append(f"💀击杀回血！恢复了{heal_amount}点生命值！")

        # 触发防具击杀回血
        old_hp = player.hp
        player.on_kill_monster()
        armor_kill_heal = player.hp - old_hp
        if armor_kill_heal > 0:
            result['logs'].append(f"🛡️防具嗜血效果恢复了{armor_kill_heal}点生命值！")

        # 移除怪物
        floor.remove_monster(monster.id)

    else:
        # 怪物反击
        monster_damage = calculate_damage(monster.atk, player.total_def)

        # 应用防具词条防御效果
        final_damage, armor_logs = calculate_damage_with_armor_defense(monster_damage, player)

        actual_damage_to_player = player.take_damage(final_damage)
        result['monster_damage'] = actual_damage_to_player

        # 添加防具效果日志
        result['logs'].extend(armor_logs)

        # 基础伤害日志
        damage_log = f"{monster.name}对你造成了{actual_damage_to_player}点伤害！"
        result['logs'].append(damage_log)

        # 应用反击伤害（武器荆棘）
        thorn_rate = player.get_thorn_damage_rate()
        if thorn_rate > 0:
            thorn_damage = int(actual_damage_to_player * thorn_rate)
            monster_hp_after_thorn = monster.take_damage(thorn_damage)
            if thorn_damage > 0:
                result['logs'].append(f"🌿武器荆棘效果对{monster.name}反弹了{thorn_damage}点伤害！")

        # 应用防具荆棘反射
        thorn_reflect_rate = player.get_armor_attribute_value('thorn_reflect')
        if thorn_reflect_rate > 0:
            reflect_damage = int(actual_damage_to_player * thorn_reflect_rate)
            monster_hp_after_reflect = monster.take_damage(reflect_damage)
            if reflect_damage > 0:
                result['logs'].append(f"🛡️防具荆棘反射对{monster.name}反弹了{reflect_damage}点伤害！")

        if not player.is_alive():
            result['logs'].append("你被击败了...")

    return result


def check_auto_interactions(player: Player, floor: Floor) -> List[Dict[str, Any]]:
    """
    检查并执行自动交互（拾取道具、上楼）
    当玩家移动到新位置时自动调用

    Args:
        player: 玩家对象
        floor: 当前楼层

    Returns:
        交互结果消息列表
    """
    messages = []

    # 检查是否在楼梯上
    if floor.stairs_pos and player.position.x == floor.stairs_pos.x and player.position.y == floor.stairs_pos.y:
        # 检查楼梯是否被怪物周围3格内限制
        if floor.is_item_or_stairs_blocked_by_monster(floor.stairs_pos):
            messages.append({'type': 'log', 'message': "怪物距离楼梯太近，无法进入下一层！"})
        else:
            # 自动进入下一层
            result = descend_floor(player, floor, floor.level)
            if result['logs']:
                messages.append({'type': 'log', 'message': result['logs'][0]})
            if result['success']:
                messages.append({'type': 'auto_descend', 'floor': floor.level + 1})

    # 检查是否有道具
    else:
        item = floor.get_item_at(player.position)
        if item:
            # 检查物品是否被怪物周围3格内限制
            if floor.is_item_or_stairs_blocked_by_monster(item.position):
                messages.append({'type': 'log', 'message': "怪物距离物品太近，无法拾取道具！"})
            else:
                # 自动拾取道具
                result = pickup_item(player, floor)
                if result['logs']:
                    for log in result['logs']:
                        messages.append({'type': 'log', 'message': log})
                if result['success']:
                    messages.append({'type': 'auto_pickup', 'item': result['item'].to_dict()})
                    messages.append({'type': 'map', 'grid': floor.to_serializable_grid(player)})

    return messages


def move_player(player: Player, direction: str, floor: Floor) -> Dict[str, Any]:
    """
    移动玩家

    Args:
        player: 玩家对象
        direction: 移动方向 ('up', 'down', 'left', 'right')
        floor: 当前楼层

    Returns:
        移动结果字典，包含：
        - success: 是否成功移动
        - new_position: 新位置
        - bumped_into: 撞到的实体类型 ('monster', 'wall', 'stairs')
        - monster: 撞到的怪物对象（如果有）
        - logs: 日志列表
    """
    result = {
        'success': False,
        'new_position': None,
        'bumped_into': None,
        'monster': None,
        'logs': []
    }

    # 计算新位置
    direction_map = {
        'up': Position(0, -1),
        'down': Position(0, 1),
        'left': Position(-1, 0),
        'right': Position(1, 0)
    }

    if direction not in direction_map:
        result['logs'].append("无效的方向")
        return result

    new_pos = player.position + direction_map[direction]

    # 检查边界
    if not (0 <= new_pos.x < floor.width and 0 <= new_pos.y < floor.height):
        result['logs'].append("无法移动到地图外")
        return result

    # 检查是否可通行
    can_move = False
    cell = floor.grid[new_pos.x][new_pos.y]

    if floor.is_passable(new_pos):
        can_move = True
    else:
        # 检查是墙、怪物还是道具
        if cell.type == CellType.WALL:
            result['bumped_into'] = 'wall'
            result['logs'].append("前方是墙壁，无法通过")
            return result
        elif cell.entity and hasattr(cell.entity, 'hp'):  # 是怪物
            result['bumped_into'] = 'monster'
            result['monster'] = cell.entity
            result['logs'].append(f"遭遇了{cell.entity.name}！")
            return result
        elif cell.type == CellType.STAIRS:
            result['bumped_into'] = 'stairs'
            result['logs'].append("发现了楼梯，按 '>' 键进入下一层")
            return result
        elif cell.entity and hasattr(cell.entity, 'effect_type'):  # 是道具
            # 允许移动到道具位置，将在自动交互中处理拾取
            can_move = True
        else:
            # 其他不可通行的情况
            return result

    # 检查是否可以移动
    if not can_move:
        return result

    # 成功移动
    result['success'] = True
    result['new_position'] = new_pos
    player.position = new_pos

    # 移动成功后检查自动交互（拾取道具、上楼）
    result['auto_interactions'] = check_auto_interactions(player, floor)

    return result


def find_empty_position(center_pos: Position, floor: Floor) -> Position:
    """
    在指定位置附近找一个空位置

    Args:
        center_pos: 中心位置
        floor: 楼层对象

    Returns:
        空位置，如果没有则返回None
    """
    # 螺旋搜索，从中心向外
    for radius in range(1, min(floor.width, floor.height)):
        # 搜索螺旋路径
        for dx, dy in [(0, -radius), (radius, 0), (0, radius), (-radius, 0)]:
            for i in range(radius * 2 + 1):
                if dx == 0:  # 垂直方向
                    x = center_pos.x + dx
                    y = center_pos.y - radius + i
                else:  # 水平方向
                    x = center_pos.x - radius + i
                    y = center_pos.y + dy

                # 检查边界
                if 0 <= x < floor.width and 0 <= y < floor.height:
                    cell = floor.grid[x][y]
                    if cell.passable and (cell.entity is None or cell.entity.symbol == '.'):
                        return Position(x, y)

    return None


def pickup_item(player: Player, floor: Floor) -> Dict[str, Any]:
    """
    拾取玩家所在位置的道具
    新增：检查房间内是否有怪物，有怪物时不能拾取

    Args:
        player: 玩家对象
        floor: 当前楼层

    Returns:
        拾取结果字典
    """
    result = {
        'success': False,
        'item': None,
        'logs': []
    }

    # 检查物品是否被怪物周围3格内限制
    item = floor.get_item_at(player.position)
    if item:
        if floor.is_item_or_stairs_blocked_by_monster(item.position):
            result['logs'].append("怪物距离物品太近，无法拾取！")
            return result
    else:
        result['logs'].append("这里没有道具可以拾取")
        return result

    result['success'] = True
    result['item'] = item

    # 初始化掉落装备变量
    old_weapon_item = None
    old_armor_item = None

    if item.effect_type == 'potion':
        # 血瓶：加入背包
        item_name = item.name
        if item_name in player.inventory:
            player.inventory[item_name] += 1
        else:
            player.inventory[item_name] = 1
        result['logs'].append(f"拾取了{item.name}")

    elif item.effect_type == 'weapon':
        # 武器：使用新的装备系统替换当前武器，旧武器掉落在当前位置
        equip_result = player.equip_weapon(item)
        old_weapon_info = equip_result['old_weapon']

        # 添加装备日志
        result['logs'].extend(equip_result['logs'])

        # 处理旧武器掉落
        if old_weapon_info['name'] and old_weapon_info['atk'] > 0:
            old_weapon_item = Item(
                symbol='↑',
                name=old_weapon_info['name'],
                effect_type='weapon',
                effect_value=old_weapon_info['atk'],
                position=player.position,
                item_id=f"dropped_weapon_{random.randint(1000, 9999)}",
                rarity=old_weapon_info['rarity'],
                attributes=old_weapon_info['attributes'].copy() if old_weapon_info['attributes'] else []
            )

    elif item.effect_type == 'armor':
        # 防具：替换当前防���，旧防具掉落在当前位置
        old_armor_name = player.armor_name
        old_armor_def = player.armor_def
        old_armor_attributes = player.armor_attributes.copy()
        old_armor_rarity = player.armor_rarity

        # 记录装备前的生命值
        old_max_hp = player.max_hp
        old_current_hp = player.hp

        player.armor_def = item.effect_value
        player.armor_name = item.name
        player.armor_attributes = item.armor_attributes.copy() if item.armor_attributes else []
        player.armor_rarity = item.rarity

        result['logs'].append(f"装备了{item.name}")
        if item.armor_attributes:
            result['logs'].append(f"防具��有度：{item.rarity}")
            for attr in item.armor_attributes:
                result['logs'].append(f"  {attr.description}")
        # 计算装备后的生命值变化
        new_max_hp = player.max_hp_with_attributes
        hp_boost = new_max_hp - old_max_hp

        # 如果有HP加成，显示相应反馈
        if hp_boost > 0:
            result['logs'].append(f"❤️生命值上限提升了{hp_boost}点！")
            # 按比例补充当前生命值
            if old_current_hp > 0:
                hp_ratio = old_current_hp / old_max_hp if old_max_hp > 0 else 1.0
                new_hp = min(new_max_hp, int(new_max_hp * hp_ratio))
                actual_heal = new_hp - old_current_hp
                if actual_heal > 0:
                    player.hp = new_hp
                    result['logs'].append(f"当前生命值补充了{actual_heal}点")

        # 创建旧防具道具
        if old_armor_name and old_armor_def > 0:
            old_armor_item = Item(
                symbol='◆',
                name=old_armor_name,
                effect_type='armor',
                effect_value=old_armor_def,
                position=player.position,
                item_id=f"dropped_armor_{random.randint(1000, 9999)}",
                rarity=old_armor_rarity,
                armor_attributes=old_armor_attributes.copy() if old_armor_attributes else []
            )

    # 从地图上移除拾取的道具
    if old_weapon_item or old_armor_item:
        # 如果有装备掉落，先移除新装备但保留格子实体
        floor.remove_item(item.item_id, clear_entity=False)

        # 处理装备掉落到地上
        if old_weapon_item:
            # 添加武器到地图
            floor.items[old_weapon_item.item_id] = old_weapon_item
            floor.grid[player.position.x][player.position.y].entity = old_weapon_item
            result['logs'].append(f"{old_weapon_item.name}掉落在地上")

        if old_armor_item:
            # 如果武器已经掉落在同一个位置，需要避免冲突
            current_entity = floor.grid[player.position.x][player.position.y].entity
            if current_entity is None or current_entity.symbol == '.':
                # 位置为空，直接放置防具
                floor.grid[player.position.x][player.position.y].entity = old_armor_item
            elif current_entity.symbol == '↑':
                # 位置已有武器，防具放置在旁边
                pos = find_empty_position(player.position, floor)
                if pos:
                    old_armor_item.position = pos
                    floor.grid[pos.x][pos.y].entity = old_armor_item
                else:
                    # 没有空位置，防具丢失
                    result['logs'].append(f"{old_armor_item.name}没有空间放置，丢失了")
            else:
                # 其他情况，直接放置
                floor.grid[player.position.x][player.position.y].entity = old_armor_item

            # 添加防具到地图
            floor.items[old_armor_item.item_id] = old_armor_item
            result['logs'].append(f"{old_armor_item.name}掉落在地上")
    else:
        # 没有装备掉落，正常移除道具并清理格子实体
        floor.remove_item(item.item_id, clear_entity=True)

    return result


def descend_floor(player: Player, floor: Floor, current_floor_level: int) -> Dict[str, Any]:
    """
    进入下一层

    Args:
        player: 玩家对象
        floor: 当前楼层
        current_floor_level: 当前层数

    Returns:
        结果字典
    """
    result = {
        'success': False,
        'logs': []
    }

    # 检查是否在楼梯上 - 使用坐标级别比较
    if (player.position.x != floor.stairs_pos.x or
        player.position.y != floor.stairs_pos.y):
        result['logs'].append(f"你必须站在楼梯上才能进入下一层（当前位置：{player.position.x}, {player.position.y}，楼梯位置：{floor.stairs_pos.x}, {floor.stairs_pos.y}）")
        return result

    # 检查楼梯是否被怪物周围3格内限制
    if floor.is_item_or_stairs_blocked_by_monster(floor.stairs_pos):
        result['logs'].append("怪物距离楼梯太近，无法上楼！")
        return result


    # 检查是否是最后一层
    if current_floor_level >= 100:
        result['logs'].append("恭喜！你已经通关了！")
        result['success'] = True
        return result

    result['success'] = True
    result['logs'].append(f"进入了第{current_floor_level + 1}层...")

    # 触发防具上楼回血
    old_hp = player.hp
    player.on_floor_change()
    floor_heal = player.hp - old_hp
    if floor_heal > 0:
        result['logs'].append(f"🛡️防具恢复效果恢复了{floor_heal}点生命值！")

    return result


# ==================== 武器锻造系统 ====================

def forge_weapon_attribute(player: Player, attribute_index: int) -> Dict[str, Any]:
    """
    锻造武器词条属性

    Args:
        player: 玩家对象
        attribute_index: 要强化的词条索引（0-based）

    Returns:
        锻造结果字典
    """
    config = config_manager.get_config()

    # 检查是否有武器
    if not player.weapon_name or player.weapon_atk <= 0:
        return {
            "success": False,
            "message": "没有装备武器，无法锻造"
        }

    # 检查词条索引是否有效
    if attribute_index < 0 or attribute_index >= len(player.weapon_attributes):
        return {
            "success": False,
            "message": "无效的词条索引"
        }

    attribute = player.weapon_attributes[attribute_index]
    current_level = attribute.level

    # 计算锻造成本和成功率
    forge_cost = calculate_forge_cost(current_level, player.weapon_rarity, player.level)
    success_rate = calculate_forge_success_rate(current_level, player.weapon_rarity)

    # 检查金币
    if player.gold < forge_cost:
        return {
            "success": False,
            "message": f"金币不足，需要{forge_cost}金币",
            "required_gold": forge_cost,
            "current_gold": player.gold
        }

    # 扣除金币
    player.gold -= forge_cost

    # 尝试锻造
    is_success = random.random() < success_rate

    if is_success:
        # 锻造成功，提升词条等级
        attribute.level += 1
        result_message = f"锻造成功！{attribute.description} 提升到 Lv.{attribute.level + 1}"

        return {
            "success": True,
            "message": result_message,
            "attribute_index": attribute_index,
            "old_level": current_level,
            "new_level": attribute.level,
            "gold_spent": forge_cost,
            "success_rate": success_rate
        }
    else:
        # 锻造失败
        result_message = f"锻造失败！{attribute.description} 仍然是 Lv.{current_level + 1}"

        return {
            "success": False,
            "message": result_message,
            "attribute_index": attribute_index,
            "current_level": current_level,
            "gold_spent": forge_cost,
            "success_rate": success_rate,
            "is_forge_failure": True  # 标识这是锻造失败（不是其他错误）
        }

def calculate_forge_cost(level: int, rarity: str, player_level: int) -> int:
    """
    计算锻造成本

    Args:
        level: 当前词条等级
        rarity: 武器稀有度
        player_level: 玩家等级

    Returns:
        锻造所需金币
    """
    config = config_manager.get_config()
    base_cost = config.FORGE_BASE_COST + level * config.FORGE_LEVEL_COST
    level_tax = player_level * 10
    rarity_multiplier = config.FORGE_RARITY_COST_MULTIPLIER.get(rarity, 1.0)
    return int((base_cost + level_tax) * rarity_multiplier)

def calculate_forge_success_rate(level: int, rarity: str) -> float:
    """
    计算锻造成功率

    Args:
        level: 当前词条等级
        rarity: 武器稀有度

    Returns:
        成功率 (0.0-1.0)
    """
    config = config_manager.get_config()
    base_success_rate = max(
        config.FORGE_MIN_SUCCESS,
        config.FORGE_BASE_SUCCESS - level * config.FORGE_SUCCESS_DECAY
    )
    rarity_bonus = config.FORGE_RARITY_SUCCESS_BONUS.get(rarity, 0.0)
    return min(0.95, base_success_rate + rarity_bonus)

def get_forge_info(player: Player) -> Dict[str, Any]:
    """
    获取锻造信息

    Args:
        player: 玩家对象

    Returns:
        锻造信息字典
    """
    if not player.weapon_name or player.weapon_atk <= 0:
        return {
            "has_weapon": False,
            "message": "没有装备武器"
        }

    forge_info = {
        "has_weapon": True,
        "weapon_name": player.weapon_name,
        "weapon_rarity": player.weapon_rarity,
        "attributes": []
    }

    for i, attr in enumerate(player.weapon_attributes):
        forge_cost = calculate_forge_cost(attr.level, player.weapon_rarity, player.level)
        success_rate = calculate_forge_success_rate(attr.level, player.weapon_rarity)
        enhanced_value = attr.get_enhanced_value()

        forge_info["attributes"].append({
            "index": i,
            "type": attr.attribute_type,
            "description": attr.description,
            "level": attr.level,
            "enhanced_value": enhanced_value,
            "base_value": attr.value,
            "forge_cost": forge_cost,
            "success_rate": success_rate
        })

    return forge_info


# ==================== 基础属性升级系统 ====================

def forge_base_attribute(player: Player, equipment_type: str) -> Dict[str, Any]:
    """
    锻造装备基础属性（攻击力/防御力）

    Args:
        player: 玩家对象
        equipment_type: 装备类型 ('weapon' 或 'armor')

    Returns:
        锻造结果字典
    """
    if equipment_type == 'weapon':
        # 检查是否有武器
        if not player.weapon_name or player.weapon_atk <= 0:
            return {
                "success": False,
                "message": "没有装备武器，无法锻造"
            }

        current_atk = player.weapon_atk
        upgrade_value = max(1, int(current_atk * 0.05))  # 5%提升，最少+1

        # 成本公式：300 + 当前攻击力×2 + 玩家等级×15
        forge_cost = 300 + current_atk * 2 + player.level * 15
        success_rate = 0.9  # 90%成功率

        # 检查金币
        if player.gold < forge_cost:
            return {
                "success": False,
                "message": f"金币不足，需要{forge_cost}金币",
                "required_gold": forge_cost,
                "current_gold": player.gold
            }

        # 扣除金币
        player.gold -= forge_cost

        # 尝试锻造
        is_success = random.random() < success_rate

        if is_success:
            # 锻造成功
            player.weapon_atk += upgrade_value
            return {
                "success": True,
                "message": f"锻造成功！武器攻击力 +{upgrade_value}（{current_atk} → {player.weapon_atk}）",
                "old_value": current_atk,
                "new_value": player.weapon_atk,
                "upgrade_value": upgrade_value,
                "gold_spent": forge_cost,
                "success_rate": success_rate
            }
        else:
            # 锻造失败
            return {
                "success": False,
                "message": f"锻造失败！武器攻击力保持 {current_atk}",
                "current_value": current_atk,
                "gold_spent": forge_cost,
                "success_rate": success_rate,
                "is_forge_failure": True
            }

    elif equipment_type == 'armor':
        # 检查是否有防具
        if not player.armor_name or player.armor_def <= 0:
            return {
                "success": False,
                "message": "没有装备防具，无法锻造"
            }

        current_def = player.armor_def
        upgrade_value = max(1, int(current_def * 0.05))  # 5%提升，最少+1

        # 成本公式：300 + 当前防御力×3 + 玩家等级×15
        forge_cost = 300 + current_def * 3 + player.level * 15
        success_rate = 0.9  # 90%成功率

        # 检查金币
        if player.gold < forge_cost:
            return {
                "success": False,
                "message": f"金币不足，需要{forge_cost}金币",
                "required_gold": forge_cost,
                "current_gold": player.gold
            }

        # 扣除金币
        player.gold -= forge_cost

        # 尝试锻造
        is_success = random.random() < success_rate

        if is_success:
            # 锻造成功
            player.armor_def += upgrade_value
            return {
                "success": True,
                "message": f"锻造成功！防具防御力 +{upgrade_value}（{current_def} → {player.armor_def}）",
                "old_value": current_def,
                "new_value": player.armor_def,
                "upgrade_value": upgrade_value,
                "gold_spent": forge_cost,
                "success_rate": success_rate
            }
        else:
            # 锻造失败
            return {
                "success": False,
                "message": f"锻造失败！防具防御力保持 {current_def}",
                "current_value": current_def,
                "gold_spent": forge_cost,
                "success_rate": success_rate,
                "is_forge_failure": True
            }

    else:
        return {
            "success": False,
            "message": "无效的装备类型"
        }


# ==================== 新增随机词条系统 ====================

def add_random_attribute(player: Player, equipment_type: str) -> Dict[str, Any]:
    """
    为装备添加随机词条

    Args:
        player: 玩家对象
        equipment_type: 装备类型 ('weapon' 或 'armor')

    Returns:
        锻造结果字典
    """
    from game_model import ATTRIBUTE_TYPES, ARMOR_ATTRIBUTE_TYPES, RARITY_CONFIG, WeaponAttribute, ArmorAttribute

    if equipment_type == 'weapon':
        # 检查是否有武器
        if not player.weapon_name or player.weapon_atk <= 0:
            return {
                "success": False,
                "message": "没有装备武器，无法锻造"
            }

        # 检查词条槽是否已满
        max_attrs = RARITY_CONFIG[player.weapon_rarity]['attr_count']
        current_count = len(player.weapon_attributes)

        if current_count >= max_attrs:
            return {
                "success": False,
                "message": f"词条已满（{current_count}/{max_attrs}），无法新增"
            }

        # 成本公式：500 + 玩家等级×25 + 现有词条数×200
        forge_cost = 500 + player.level * 25 + current_count * 200
        success_rate = 0.7  # 70%成功率

        # 检查金币
        if player.gold < forge_cost:
            return {
                "success": False,
                "message": f"金币不足，需要{forge_cost}金币",
                "required_gold": forge_cost,
                "current_gold": player.gold
            }

        # 扣除金币
        player.gold -= forge_cost

        # 尝试锻造
        is_success = random.random() < success_rate

        if is_success:
            # 锻造成功，生成新词条
            # 获取已有词条类型
            existing_types = {attr.attribute_type for attr in player.weapon_attributes}

            # 排除已有词条类型
            available_types = {k: v for k, v in ATTRIBUTE_TYPES.items() if k not in existing_types}

            if not available_types:
                return {
                    "success": False,
                    "message": "没有可用的词条类型，无法新增",
                    "is_forge_failure": True
                }

            # 加权随机选择
            attr_type = random.choices(
                list(available_types.keys()),
                weights=[v['weight'] for v in available_types.values()]
            )[0]

            attr_config = ATTRIBUTE_TYPES[attr_type]

            # 基于玩家当前楼层计算数值（假设玩家等级约等于楼层进度），统一保留两位小数
            estimated_floor = player.level  # 简化处理
            base_value = attr_config['base_value'] + estimated_floor * attr_config['scale']
            rarity_multiplier = RARITY_CONFIG[player.weapon_rarity]['multiplier']
            final_value = round(base_value * rarity_multiplier, 2)

            # 创建属性描述
            description = attr_config['description']
            if '{value*100}' in description:
                description = description.replace('{value*100}', f'{final_value*100:.1f}')
            else:
                # 非百分比词条：按整数四舍五入展示，避免出现长小数
                value_str = str(int(round(final_value)))
                description = description.format(value=value_str)

            # 创建新词条
            new_attr = WeaponAttribute(
                attribute_type=attr_type,
                value=final_value,
                description=description,
                level=0
            )

            player.weapon_attributes.append(new_attr)

            return {
                "success": True,
                "message": f"成功添加词条：{new_attr.description}（{current_count+1}/{max_attrs}）",
                "new_attribute": new_attr.to_dict(),
                "gold_spent": forge_cost,
                "success_rate": success_rate
            }
        else:
            # 锻造失败
            return {
                "success": False,
                "message": "添加词条失败！",
                "gold_spent": forge_cost,
                "success_rate": success_rate,
                "is_forge_failure": True
            }

    elif equipment_type == 'armor':
        # 检查是否有防具
        if not player.armor_name or player.armor_def <= 0:
            return {
                "success": False,
                "message": "没有装备防具，无法锻造"
            }

        # 检查词条槽是否已满
        max_attrs = RARITY_CONFIG[player.armor_rarity]['attr_count']
        current_count = len(player.armor_attributes)

        if current_count >= max_attrs:
            return {
                "success": False,
                "message": f"词条已满（{current_count}/{max_attrs}），无法新增"
            }

        # 成本公式：500 + 玩家等级×25 + 现有词条数×200
        forge_cost = 500 + player.level * 25 + current_count * 200
        success_rate = 0.7  # 70%成功率

        # 检查金币
        if player.gold < forge_cost:
            return {
                "success": False,
                "message": f"金币不足，需要{forge_cost}金币",
                "required_gold": forge_cost,
                "current_gold": player.gold
            }

        # 扣除金币
        player.gold -= forge_cost

        # 尝试锻造
        is_success = random.random() < success_rate

        if is_success:
            # 锻造成功，生成新词条
            # 获取已有词条类型
            existing_types = {attr.attribute_type for attr in player.armor_attributes}

            # 排除已有词条类型
            available_types = {k: v for k, v in ARMOR_ATTRIBUTE_TYPES.items() if k not in existing_types}

            if not available_types:
                return {
                    "success": False,
                    "message": "没有可用的词条类型，无法新增",
                    "is_forge_failure": True
                }

            # 加权随机选择
            attr_type = random.choices(
                list(available_types.keys()),
                weights=[v['weight'] for v in available_types.values()]
            )[0]

            attr_config = ARMOR_ATTRIBUTE_TYPES[attr_type]

            # 基于玩家当前等级计算数值
            estimated_floor = player.level
            base_value = attr_config['base_value'] + estimated_floor * attr_config['scale']
            rarity_multiplier = RARITY_CONFIG[player.armor_rarity]['multiplier']
            final_value = round(base_value * rarity_multiplier, 2)

            # 创建属性描述
            description = attr_config['description']
            if '{value*100}' in description:
                description = description.replace('{value*100}', f'{final_value*100:.1f}')
            else:
                # 非百分比词条：按整数四舍五入展示，避免出现长小数
                value_str = str(int(round(final_value)))
                description = description.format(value=value_str)

            # 创建新词条
            new_attr = ArmorAttribute(
                attribute_type=attr_type,
                value=final_value,
                description=description,
                level=0
            )

            player.armor_attributes.append(new_attr)

            return {
                "success": True,
                "message": f"成功添加词条：{new_attr.description}（{current_count+1}/{max_attrs}）",
                "new_attribute": new_attr.to_dict(),
                "gold_spent": forge_cost,
                "success_rate": success_rate
            }
        else:
            # 锻造失败
            return {
                "success": False,
                "message": "添加词条失败！",
                "gold_spent": forge_cost,
                "success_rate": success_rate,
                "is_forge_failure": True
            }

    else:
        return {
            "success": False,
            "message": "无效的装备类型"
        }


# ==================== 重铸词条系统 ====================

def reforge_attribute(player: Player, equipment_type: str, attribute_index: int) -> Dict[str, Any]:
    """
    重铸词条：保持等级不变，随机更换词条类型

    Args:
        player: 玩家对象
        equipment_type: 装备类型 ('weapon' 或 'armor')
        attribute_index: 要重铸的词条索引

    Returns:
        锻造结果字典
    """
    from game_model import ATTRIBUTE_TYPES, ARMOR_ATTRIBUTE_TYPES, RARITY_CONFIG, WeaponAttribute, ArmorAttribute

    if equipment_type == 'weapon':
        # 检查是否有武器
        if not player.weapon_name or player.weapon_atk <= 0:
            return {
                "success": False,
                "message": "没有装备武器，无法锻造"
            }

        # 检查词条索引是否有效
        if attribute_index < 0 or attribute_index >= len(player.weapon_attributes):
            return {
                "success": False,
                "message": "无效的词条索引"
            }

        old_attr = player.weapon_attributes[attribute_index]

        # 成本公式：400 + 词条等级×100 + 玩家等级×20
        forge_cost = 400 + old_attr.level * 100 + player.level * 20
        success_rate = 0.8  # 80%成功率

        # 检查金币
        if player.gold < forge_cost:
            return {
                "success": False,
                "message": f"金币不足，需要{forge_cost}金币",
                "required_gold": forge_cost,
                "current_gold": player.gold
            }

        # 扣除金币
        player.gold -= forge_cost

        # 尝试锻造
        is_success = random.random() < success_rate

        if is_success:
            # 锻造成功，重铸词条
            # 获取已有词条类型（排除当前要重铸的词条）
            existing_types = {attr.attribute_type for i, attr in enumerate(player.weapon_attributes) if i != attribute_index}

            # 排除已有词条类型
            available_types = {k: v for k, v in ATTRIBUTE_TYPES.items() if k not in existing_types}

            if not available_types:
                # 如果没有可用类型，至少允许保留当前类型
                available_types = ATTRIBUTE_TYPES

            # 加权随机选择新类型
            new_attr_type = random.choices(
                list(available_types.keys()),
                weights=[v['weight'] for v in available_types.values()]
            )[0]

            attr_config = ATTRIBUTE_TYPES[new_attr_type]

            # 基于玩家当前等级计算数值
            estimated_floor = player.level
            base_value = attr_config['base_value'] + estimated_floor * attr_config['scale']
            rarity_multiplier = RARITY_CONFIG[player.weapon_rarity]['multiplier']
            final_value = round(base_value * rarity_multiplier, 2)

            # 创建属性描述
            description = attr_config['description']
            if '{value*100}' in description:
                description = description.replace('{value*100}', f'{final_value*100:.1f}')
            else:
                # 其它数值统一最多保留两位小数，并去掉多余的 0
                value_str = f"{final_value:.2f}".rstrip('0').rstrip('.')
                description = description.format(value=value_str)

            # 创建新词条（保留等级）
            new_attr = WeaponAttribute(
                attribute_type=new_attr_type,
                value=final_value,
                description=description,
                level=old_attr.level  # 保留等级
            )

            # 替换词条
            player.weapon_attributes[attribute_index] = new_attr

            return {
                "success": True,
                "message": f"重铸成功！{old_attr.description} → {new_attr.description}（Lv.{new_attr.level + 1}）",
                "old_attribute": old_attr.to_dict(),
                "new_attribute": new_attr.to_dict(),
                "gold_spent": forge_cost,
                "success_rate": success_rate
            }
        else:
            # 锻造失败
            return {
                "success": False,
                "message": f"重铸失败！保留词条：{old_attr.description}",
                "current_attribute": old_attr.to_dict(),
                "gold_spent": forge_cost,
                "success_rate": success_rate,
                "is_forge_failure": True
            }

    elif equipment_type == 'armor':
        # 检查是否有防具
        if not player.armor_name or player.armor_def <= 0:
            return {
                "success": False,
                "message": "没有装备防具，无法锻造"
            }

        # 检查词条索引是否有效
        if attribute_index < 0 or attribute_index >= len(player.armor_attributes):
            return {
                "success": False,
                "message": "无效的词条索引"
            }

        old_attr = player.armor_attributes[attribute_index]

        # 成本公式：400 + 词条等级×100 + 玩家等级×20
        forge_cost = 400 + old_attr.level * 100 + player.level * 20
        success_rate = 0.8  # 80%成功率

        # 检查金币
        if player.gold < forge_cost:
            return {
                "success": False,
                "message": f"金币不足，需要{forge_cost}金币",
                "required_gold": forge_cost,
                "current_gold": player.gold
            }

        # 扣除金币
        player.gold -= forge_cost

        # 尝试锻造
        is_success = random.random() < success_rate

        if is_success:
            # 锻造成功，重铸词条
            # 获取已有词条类型（排除当前要重铸的词条）
            existing_types = {attr.attribute_type for i, attr in enumerate(player.armor_attributes) if i != attribute_index}

            # 排除已有词条类型
            available_types = {k: v for k, v in ARMOR_ATTRIBUTE_TYPES.items() if k not in existing_types}

            if not available_types:
                # 如果没有可用类型，至少允许保留当前类型
                available_types = ARMOR_ATTRIBUTE_TYPES

            # 加权随机选择新类型
            new_attr_type = random.choices(
                list(available_types.keys()),
                weights=[v['weight'] for v in available_types.values()]
            )[0]

            attr_config = ARMOR_ATTRIBUTE_TYPES[new_attr_type]

            # 基于玩家当前等级计算数值
            estimated_floor = player.level
            base_value = attr_config['base_value'] + estimated_floor * attr_config['scale']
            rarity_multiplier = RARITY_CONFIG[player.armor_rarity]['multiplier']
            final_value = round(base_value * rarity_multiplier, 2)

            # 创建属性描述
            description = attr_config['description']
            if '{value*100}' in description:
                description = description.replace('{value*100}', f'{final_value*100:.1f}')
            else:
                # 其它数值统一最多保留两位小数，并去掉多余的 0
                value_str = f"{final_value:.2f}".rstrip('0').rstrip('.')
                description = description.format(value=value_str)

            # 创建新词条（保留等级）
            new_attr = ArmorAttribute(
                attribute_type=new_attr_type,
                value=final_value,
                description=description,
                level=old_attr.level  # 保留等级
            )

            # 替换词条
            player.armor_attributes[attribute_index] = new_attr

            return {
                "success": True,
                "message": f"重铸成功！{old_attr.description} → {new_attr.description}（Lv.{new_attr.level + 1}）",
                "old_attribute": old_attr.to_dict(),
                "new_attribute": new_attr.to_dict(),
                "gold_spent": forge_cost,
                "success_rate": success_rate
            }
        else:
            # 锻造失败
            return {
                "success": False,
                "message": f"重铸失败！保留词条：{old_attr.description}",
                "current_attribute": old_attr.to_dict(),
                "gold_spent": forge_cost,
                "success_rate": success_rate,
                "is_forge_failure": True
            }

    else:
        return {
            "success": False,
            "message": "无效的装备类型"
        }


# ==================== 扩展锻造信息系统 ====================

def get_forge_info_extended(player: Player) -> Dict[str, Any]:
    """
    获取完整的锻造信息，包括武器和防具

    Args:
        player: 玩家对象

    Returns:
        锻造信息字典，包含武器和防具的完整信息
    """
    from game_model import RARITY_CONFIG

    # 武器信息
    weapon_info = {
        "has_weapon": bool(player.weapon_name) and player.weapon_atk > 0,
        "weapon_name": player.weapon_name or "",
        "weapon_atk": player.weapon_atk,
        "weapon_rarity": player.weapon_rarity,
        "attributes": [],
        "max_attributes": 0
    }

    if weapon_info["has_weapon"]:
        weapon_info["max_attributes"] = RARITY_CONFIG[player.weapon_rarity]['attr_count']
        weapon_info["attributes"] = [attr.to_dict() for attr in player.weapon_attributes]

    # 防具信息
    armor_info = {
        "has_armor": bool(player.armor_name) and player.armor_def > 0,
        "armor_name": player.armor_name or "",
        "armor_def": player.armor_def,
        "armor_rarity": player.armor_rarity,
        "attributes": [],
        "max_attributes": 0
    }

    if armor_info["has_armor"]:
        armor_info["max_attributes"] = RARITY_CONFIG[player.armor_rarity]['attr_count']
        armor_info["attributes"] = [attr.to_dict() for attr in player.armor_attributes]

    return {
        "weapon": weapon_info,
        "armor": armor_info,
        "gold": player.gold,
        "player_level": player.level
    }


# ==================== 商人交易系统 ====================

def handle_trade_request(player: Player, floor: Floor, item_name: str) -> dict:
    """处理购买请求"""
    if not floor.is_merchant_floor:
        return {"success": False, "message": "这里没有商人"}

    # 查找商品
    merchant_item = None
    for item in floor.merchant.inventory:
        if item.name == item_name:
            merchant_item = item
            break

    if not merchant_item:
        return {"success": False, "message": "商人没有这个物品"}

    # 检查金币
    if player.gold < merchant_item.price:
        return {"success": False, "message": "金币不足"}

    # 执行交易
    player.gold -= merchant_item.price

    equip_message = ""
    # 添加物品到背包或装备
    if merchant_item.effect_type == "potion":
        player.inventory[merchant_item.name] = player.inventory.get(merchant_item.name, 0) + 1
    elif merchant_item.effect_type == "weapon":
        purchased_weapon = Item(
            symbol='↑',
            name=merchant_item.name,
            effect_type='weapon',
            effect_value=merchant_item.effect_value,
            position=player.position,
            rarity=merchant_item.rarity or 'common',
            attributes=merchant_item.attributes.copy() if merchant_item.attributes else [],
            base_name=merchant_item.base_name or merchant_item.name
        )
        equip_result = player.equip_weapon(purchased_weapon)
        # 商店内不处理旧武器掉落，避免干扰商人布局
        if equip_result['logs']:
            # 将第一条装备日志作为额外信息返回
            equip_message = equip_result['logs'][0]
        else:
            equip_message = ""
    elif merchant_item.effect_type == "armor":
        # 记录装备前的生命值
        old_max_hp = player.max_hp_with_attributes
        old_current_hp = player.hp

        # 装备防具
        player.armor_def = merchant_item.effect_value
        player.armor_name = merchant_item.name
        player.armor_attributes = merchant_item.attributes.copy() if merchant_item.attributes else []
        player.armor_rarity = merchant_item.rarity or 'common'

        # 计算装备后的生命值变化
        new_max_hp = player.max_hp_with_attributes
        hp_boost = new_max_hp - old_max_hp

        equip_message = f"装备了{merchant_item.name}"
        if merchant_item.rarity and merchant_item.rarity != 'common':
            equip_message += f"（{merchant_item.rarity}）"
        if hp_boost > 0:
            equip_message += f"，生命值上限提升了{hp_boost}点！"
            # 按比例补充当前生命值
            if old_current_hp > 0:
                hp_ratio = old_current_hp / old_max_hp if old_max_hp > 0 else 1.0
                new_hp = min(new_max_hp, int(new_max_hp * hp_ratio))
                actual_heal = new_hp - old_current_hp
                if actual_heal > 0:
                    player.hp = new_hp
                    equip_message += f"当前生命值补充了{actual_heal}点！"

    response = {
        "success": True,
        "message": f"购买了{merchant_item.name}",
        "item": merchant_item,
        "new_gold": player.gold
    }
    if equip_message:
        response["message"] += f"（{equip_message}）"
    return response

def get_merchant_info(player: Player, floor: Floor) -> dict:
    """获取商人信息（包含锻造信息）"""
    if not floor.is_merchant_floor:
        return {"has_merchant": False}

    return {
        "has_merchant": True,
        "merchant": {
            "name": floor.merchant.name,
            "inventory": [
                {
                    "name": item.name,
                    "type": item.effect_type,
                    "value": item.effect_value,
                    "price": item.price,
                    "rarity": item.rarity,
                    "attributes": [
                        attr.to_dict() for attr in (item.attributes or [])
                    ]
                }
                for item in floor.merchant.inventory
            ]
        },
        "gold": player.gold,
        "forge": get_forge_info_extended(player)  # 新增：添加锻造信息
    }

