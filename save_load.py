import json
import os
from typing import Dict, Any, Optional
from game_model import Player, Floor, Monster, Item, Position
from map_generator import generate_floor


SAVE_FILE = 'save.json'


def save_game(player: Player, floor: Floor, floor_level: int) -> bool:
    """
    保存游戏状态到JSON文件

    Args:
        player: 玩家对象
        floor: 当前楼层
        floor_level: 当前层数

    Returns:
        是否保存成功
    """
    try:
        # 序列化游戏状态
        save_data = {
            'player': {
                'hp': player.hp,
                'max_hp': player.max_hp,
                'atk': player.atk,
                'defense': player.defense,
                'exp': player.exp,
                'level': player.level,
                'gold': player.gold,
                'position': {'x': player.position.x, 'y': player.position.y},
                'weapon_atk': player.weapon_atk,
                'weapon_name': player.weapon_name,
                'armor_def': player.armor_def,
                'armor_name': player.armor_name,
                'inventory': player.inventory
            },
            'current_floor': {
                'level': floor.level,
                'width': floor.width,
                'height': floor.height,
                'player_start_pos': {'x': floor.player_start_pos.x, 'y': floor.player_start_pos.y},
                'stairs_pos': {'x': floor.stairs_pos.x, 'y': floor.stairs_pos.y} if floor.stairs_pos else None
            },
            'floor_level': floor_level
        }

        # 保存到文件
        with open(SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)

        print(f"游戏已保存到 {SAVE_FILE}")
        return True

    except Exception as e:
        print(f"保存游戏失败: {e}")
        return False


def load_player(data: Dict[str, Any]) -> Player:
    """
    从保存的数据重建Player对象

    Args:
        data: 玩家数据字典

    Returns:
        Player对象
    """
    player = Player()
    player.hp = data['hp']
    player.max_hp = data['max_hp']
    player.atk = data['atk']
    player.defense = data['defense']
    player.exp = data['exp']
    player.level = data['level']
    player.gold = data['gold']
    player.position = Position(data['position']['x'], data['position']['y'])
    player.weapon_atk = data.get('weapon_atk', 0)
    player.weapon_name = data.get('weapon_name')
    player.armor_def = data.get('armor_def', 0)
    player.armor_name = data.get('armor_name')
    player.inventory = data['inventory']

    return player


def load_game() -> Optional[Dict[str, Any]]:
    """
    从JSON文件加载游戏状态

    Returns:
        游戏状态字典，包含player、current_floor、floor_level
        如果加载失败返回None
    """
    if not os.path.exists(SAVE_FILE):
        print("存档文件不存在")
        return None

    try:
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            save_data = json.load(f)

        # 重建Player对象
        player_data = save_data['player']
        player = load_player(player_data)

        # 重建Floor对象（当前楼层）
        floor_data = save_data['current_floor']
        floor_level = save_data['floor_level']

        # 重新生成当前楼层（为了恢复怪物、道具、地图完整状态）
        current_floor = generate_floor(floor_level)

        # 恢复玩家位置（保持位置一致）
        player.position = Position(
            player_data['position']['x'],
            player_data['position']['y']
        )

        print(f"游戏已从 {SAVE_FILE} 加载 (第{floor_level}层)")

        return {
            'player': player,
            'current_floor': current_floor,
            'floor_level': floor_level
        }

    except Exception as e:
        print(f"加载游戏失败: {e}")
        return None


def delete_save() -> bool:
    """
    删除存档文件

    Returns:
        是否删除成功
    """
    try:
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
            print(f"存档文件已删除")
            return True
        return False
    except Exception as e:
        print(f"删除存档失败: {e}")
        return False

def archive_exists() -> bool:
    """
    检查存档文件是否存在

    Returns:
        是否存在存档
    """
    return os.path.exists(SAVE_FILE)
