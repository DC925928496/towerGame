from typing import List, Optional, Dict, Any
import random
from game_model import Player, Monster, Floor, Position, CellType, Item, Cell

# 导入新的工具类和配置
from utils.position_utils import PositionUtils
from utils.game_utils import GameUtils
from config.game_config import config_manager


def calculate_damage(atk: int, defense: int) -> int:
    """
    计算伤害 - 使用配置化的最小伤害值
    伤害 = max(最小伤害, 攻击方.atk - 防御方.def)

    Args:
        atk: 攻击力
        defense: 防御力

    Returns:
        造成的伤害值
    """
    config = config_manager.get_config()
    return max(config.MIN_DAMAGE, atk - defense)


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

    # 玩家攻击
    damage = calculate_damage(player.total_atk, monster.defense)
    actual_damage = monster.take_damage(damage)
    result['player_damage'] = actual_damage

    result['logs'].append(f"你对{monster.name}造成了{actual_damage}点伤害！")

    if not monster.is_alive():
        # 怪物死亡
        result['monster_dead'] = True
        result['exp_gained'] = monster.exp
        result['gold_gained'] = monster.gold

        result['logs'].append(f"你击败了{monster.name}！")
        result['logs'].append(f"获得了{monster.exp}点经验值和{monster.gold}金币")

        # 获得经验值和升级
        level_up_logs = player.gain_exp(monster.exp)
        result['level_up_logs'] = level_up_logs
        result['logs'].extend(level_up_logs)

        # 获得金币
        player.gold += monster.gold

        # 移除怪物
        floor.remove_monster(monster.id)

    else:
        # 怪物反击
        monster_damage = calculate_damage(monster.atk, player.total_def)
        actual_damage_to_player = player.take_damage(monster_damage)
        result['monster_damage'] = actual_damage_to_player

        result['logs'].append(f"{monster.name}对你造成了{actual_damage_to_player}点伤害！")

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

    # 保存旧装备信息
    old_weapon_name = None
    old_weapon_atk = 0
    old_armor_name = None
    old_armor_def = 0

    if item.effect_type == 'potion':
        # 血瓶：加入背包
        item_name = item.name
        if item_name in player.inventory:
            player.inventory[item_name] += 1
        else:
            player.inventory[item_name] = 1

        result['logs'].append(f"拾取了{item.name}")

    elif item.effect_type == 'weapon':
        # 武器：替换当前武器，旧武器掉落在当前位置
        old_weapon_name = player.weapon_name
        old_weapon_atk = player.weapon_atk

        player.weapon_atk = item.effect_value
        player.weapon_name = item.name

        result['logs'].append(f"装备了{item.name}")

    elif item.effect_type == 'armor':
        # 防具：替换当前防具，旧防具掉落在当前位置
        old_armor_name = player.armor_name
        old_armor_def = player.armor_def

        player.armor_def = item.effect_value
        player.armor_name = item.name

        result['logs'].append(f"装备了{item.name}")

    # 从地图上移除道具
    floor.remove_item(item.item_id)

    # 处理旧装备掉落（如果有）
    if old_weapon_name and old_weapon_atk > 0:
        # 创建旧武器道具
        old_weapon_item = Item(
            symbol='↑',
            name=old_weapon_name,
            effect_type='weapon',
            effect_value=old_weapon_atk,
            position=player.position,
            item_id=f"dropped_weapon_{random.randint(1000, 9999)}"
        )
        # 添加到地图
        floor.items[old_weapon_item.item_id] = old_weapon_item
        floor.grid[player.position.x][player.position.y] = Cell(CellType.EMPTY, passable=True, entity=old_weapon_item)
        result['logs'].append(f"{old_weapon_name}掉落在地上")

    if old_armor_name and old_armor_def > 0:
        # 创建旧防具道具
        old_armor_item = Item(
            symbol='◆',
            name=old_armor_name,
            effect_type='armor',
            effect_value=old_armor_def,
            position=player.position,
            item_id=f"dropped_armor_{random.randint(1000, 9999)}"
        )
        # 添加到地图
        floor.items[old_armor_item.item_id] = old_armor_item
        floor.grid[player.position.x][player.position.y] = Cell(CellType.EMPTY, passable=True, entity=old_armor_item)
        result['logs'].append(f"{old_armor_name}掉落在地上")

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

    result['logs'].append(f"调试：成功检测到楼梯位置！")

    # 检查是否是最后一层
    if current_floor_level >= 100:
        result['logs'].append("恭喜！你已经通关了！")
        result['success'] = True
        return result

    result['success'] = True
    result['logs'].append(f"进入了第{current_floor_level + 1}层...")

    return result

