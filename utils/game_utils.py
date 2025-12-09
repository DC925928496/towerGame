"""
游戏通用函数和工具类

提供游戏中常用的计算和验证函数，消除重复代码
"""

import random
from typing import Dict, List, Any, Optional
from .position_utils import Position


class GameUtils:
    """游戏通用工具类"""

    @staticmethod
    def calculate_monster_stats(floor_level: int, base_multiplier: float = 1.15) -> Dict[str, int]:
        """
        计算怪物属性

        Args:
            floor_level: 楼层级别
            base_multiplier: 基础增长倍数

        Returns:
            包含怪物属性的字典
        """
        multiplier = base_multiplier ** floor_level
        return {
            'hp': int(100 * multiplier),
            'atk': int(10 * multiplier),
            'def': int(5 * multiplier),
            'value': int(50 * multiplier)
        }

    @staticmethod
    def calculate_damage(attacker_atk: int, defender_def: int) -> int:
        """
        计算战斗伤害

        Args:
            attacker_atk: 攻击者攻击力
            defender_def: 防守者防御力

        Returns:
            伤害值
        """
        return max(1, attacker_atk - defender_def)

    @staticmethod
    def roll_random_choice_with_weights(items: List[Dict[str, Any]]) -> str:
        """
        根据权重随机选择物品

        Args:
            items: 物品列表，每个字典包含'type'和'weight'字段

        Returns:
            选中的物品类型
        """
        total_weight = sum(item['weight'] for item in items)
        roll = random.randint(1, total_weight)

        current_weight = 0
        for item in items:
            current_weight += item['weight']
            if roll <= current_weight:
                return item['type']

        return items[-1]['type']  # 默认返回最后一个

    @staticmethod
    def generate_random_name(prefixes: List[str], suffixes: List[str]) -> str:
        """
        生成随机名称

        Args:
            prefixes: 前缀列表
            suffixes: 后缀列表

        Returns:
            生成的名称
        """
        return f"{random.choice(prefixes)}{random.choice(suffixes)}"

    @staticmethod
    def validate_game_data(data: Dict[str, Any], required_keys: List[str]) -> bool:
        """
        验证游戏数据是否包含必需的字段

        Args:
            data: 要验证的数据字典
            required_keys: 必需的键列表

        Returns:
            验证是否通过
        """
        return all(key in data for key in required_keys)

    @staticmethod
    def deep_merge_dict(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
        """
        深度合并两个字典

        Args:
            dict1: 第一个字典
            dict2: 第二个字典

        Returns:
            合并后的字典
        """
        result = dict1.copy()

        for key, value in dict2.items():
            if (key in result and
                isinstance(result[key], dict) and
                isinstance(value, dict)):
                result[key] = GameUtils.deep_merge_dict(result[key], value)
            else:
                result[key] = value

        return result

    @staticmethod
    def clamp_value(value: int, min_val: int, max_val: int) -> int:
        """
        将数值限制在指定范围内

        Args:
            value: 原始值
            min_val: 最小值
            max_val: 最大值

        Returns:
            限制后的值
        """
        return max(min_val, min(value, max_val))

    @staticmethod
    def is_lucky_chance(chance: float) -> bool:
        """
        判断是否触发概率事件

        Args:
            chance: 概率 (0.0 - 1.0)

        Returns:
            是否触发
        """
        return random.random() < chance

    @staticmethod
    def find_empty_positions(grid: List[List[str]],
                           symbol: str = ' ') -> List[Position]:
        """
        找到网格中的空位置

        Args:
            grid: 二维网格
            symbol: 空位置的符号

        Returns:
            空位置列表
        """
        empty_positions = []
        for y, row in enumerate(grid):
            for x, cell in enumerate(row):
                if cell == symbol:
                    empty_positions.append(Position(x, y))
        return empty_positions

    @staticmethod
    def count_symbol_in_grid(grid: List[List[str]], symbol: str) -> int:
        """
        统计网格中特定符号的数量

        Args:
            grid: 二维网格
            symbol: 要统计的符号

        Returns:
            符号数量
        """
        return sum(row.count(symbol) for row in grid)

    @staticmethod
    def get_symbol_at_position(grid: List[List[str]], pos: Position) -> str:
        """
        获取指定位置的符号

        Args:
            grid: 二维网格
            pos: 位置

        Returns:
            符号，如果位置无效返回空字符串
        """
        if (0 <= pos.y < len(grid) and
            0 <= pos.x < len(grid[0])):
            return grid[pos.y][pos.x]
        return ''

    @staticmethod
    def set_symbol_at_position(grid: List[List[str]],
                             pos: Position,
                             symbol: str) -> bool:
        """
        在指定位置设置符号

        Args:
            grid: 二维网格
            pos: 位置
            symbol: 符号

        Returns:
            设置是否成功
        """
        if (0 <= pos.y < len(grid) and
            0 <= pos.x < len(grid[0])):
            grid[pos.y][pos.x] = symbol
            return True
        return False


class ItemUtils:
    """物品相关工具类"""

    @staticmethod
    def get_item_stats(item_name: str) -> Dict[str, int]:
        """
        获取物品属性

        Args:
            item_name: 物品名称

        Returns:
            物品属性字典
        """
        item_stats = {
            # 武器类
            "木剑": {"atk": 5, "type": "weapon", "value": 10},
            "铁剑": {"atk": 10, "type": "weapon", "value": 25},
            "钢剑": {"atk": 15, "type": "weapon", "value": 50},
            "魔法剑": {"atk": 20, "type": "weapon", "value": 100},

            # 防具类
            "布甲": {"def": 3, "type": "armor", "value": 10},
            "皮甲": {"def": 6, "type": "armor", "value": 25},
            "铁甲": {"def": 9, "type": "armor", "value": 50},
            "魔法甲": {"def": 12, "type": "armor", "value": 100},

            # 消耗品类（药瓶）
            "小药瓶": {"hp": 50, "type": "potion", "value": 20},
            "大药瓶": {"hp": 150, "type": "potion", "value": 50},
        }

        return item_stats.get(item_name, {"atk": 0, "def": 0, "hp": 0, "type": "unknown", "value": 0})

    @staticmethod
    def is_potion(item_name: str) -> bool:
        """判断是否为消耗品"""
        stats = ItemUtils.get_item_stats(item_name)
        return stats["type"] == "potion"

    @staticmethod
    def is_weapon(item_name: str) -> bool:
        """判断是否为武器"""
        stats = ItemUtils.get_item_stats(item_name)
        return stats["type"] == "weapon"

    @staticmethod
    def is_armor(item_name: str) -> bool:
        """判断是否为防具"""
        stats = ItemUtils.get_item_stats(item_name)
        return stats["type"] == "armor"


class ValidationUtils:
    """验证工具类"""

    @staticmethod
    def validate_position_grid(pos: Position, grid: List[List[str]]) -> bool:
        """验证位置是否在网格内"""
        return (0 <= pos.y < len(grid) and
                0 <= pos.x < len(grid[0]) if grid else False)

    @staticmethod
    def validate_room_coordinations(rooms: List[Dict[str, int]]) -> bool:
        """验证房间坐标是否合理"""
        if not rooms:
            return True

        grid_size = 15  # 默认网格大小
        for room in rooms:
            if not all(key in room for key in ['x', 'y', 'w', 'h']):
                return False
            if (room['x'] < 0 or room['y'] < 0 or
                room['w'] <= 0 or room['h'] <= 0):
                return False
            if (room['x'] + room['w'] > grid_size or
                room['y'] + room['h'] > grid_size):
                return False

        return True
