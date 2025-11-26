"""
位置和距离计算工具类

提供游戏中位置相关的常用计算函数，消除代码重复
"""

from typing import Tuple
from dataclasses import dataclass


@dataclass
class Position:
    """位置数据类，优化后使用__slots__减少内存占用"""
    x: int
    y: int

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __eq__(self, other) -> bool:
        if not isinstance(other, Position):
            return False
        return self.x == other.x and self.y == other.y

    def __add__(self, other: 'Position') -> 'Position':
        """位置相加运算符"""
        return Position(self.x + other.x, self.y + other.y)

    def __repr__(self) -> str:
        return f"Position({self.x}, {self.y})"


class PositionUtils:
    """位置工具类，提供距离计算、位置验证等通用功能"""

    @staticmethod
    def manhattan_distance(pos1: Position, pos2: Position) -> int:
        """
        计算曼哈顿距离

        Args:
            pos1: 位置1
            pos2: 位置2

        Returns:
            曼哈顿距离
        """
        return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)

    @staticmethod
    def euclidean_distance(pos1: Position, pos2: Position) -> float:
        """
        计算欧几里得距离

        Args:
            pos1: 位置1
            pos2: 位置2

        Returns:
            欧几里得距离
        """
        dx = pos1.x - pos2.x
        dy = pos1.y - pos2.y
        return (dx * dx + dy * dy) ** 0.5

    @staticmethod
    def is_valid_position(grid_size: int, pos: Position) -> bool:
        """
        检查位置是否在有效范围内

        Args:
            grid_size: 网格大小
            pos: 要检查的位置

        Returns:
            位置是否有效
        """
        return 0 <= pos.x < grid_size and 0 <= pos.y < grid_size

    @staticmethod
    def get_neighbors(pos: Position, grid_size: int) -> list[Position]:
        """
        获取位置的所有邻居（上下左右）

        Args:
            pos: 中心位置
            grid_size: 网格大小

        Returns:
            邻居位置列表
        """
        neighbors = []
        # 上
        if pos.y > 0:
            neighbors.append(Position(pos.x, pos.y - 1))
        # 下
        if pos.y < grid_size - 1:
            neighbors.append(Position(pos.x, pos.y + 1))
        # 左
        if pos.x > 0:
            neighbors.append(Position(pos.x - 1, pos.y))
        # 右
        if pos.x < grid_size - 1:
            neighbors.append(Position(pos.x + 1, pos.y))

        return neighbors

    @staticmethod
    def get_adjacent_positions(pos: Position, grid_size: int) -> list[Position]:
        """获取邻居位置（别名方法）"""
        return PositionUtils.get_neighbors(pos, grid_size)

    @staticmethod
    def position_to_tuple(pos: Position) -> Tuple[int, int]:
        """将位置对象转换为元组"""
        return (pos.x, pos.y)

    @staticmethod
    def tuple_to_position(coord: Tuple[int, int]) -> Position:
        """将元组转换为位置对象"""
        return Position(coord[0], coord[1])

    @staticmethod
    def are_positions_adjacent(pos1: Position, pos2: Position) -> bool:
        """
        检查两个位置是否相邻

        Args:
            pos1: 位置1
            pos2: 位置2

        Returns:
            是否相邻
        """
        return PositionUtils.manhattan_distance(pos1, pos2) == 1

    @staticmethod
    def find_positions_within_distance(
        center: Position,
        max_distance: int,
        grid_size: int
    ) -> list[Position]:
        """
        找到指定距离内的所有位置

        Args:
            center: 中心位置
            max_distance: 最大距离
            grid_size: 网格大小

        Returns:
            距离内的位置列表
        """
        positions = []
        for x in range(max(0, center.x - max_distance),
                      min(grid_size, center.x + max_distance + 1)):
            for y in range(max(0, center.y - max_distance),
                          min(grid_size, center.y + max_distance + 1)):
                pos = Position(x, y)
                if PositionUtils.manhattan_distance(center, pos) <= max_distance:
                    positions.append(pos)

        return positions