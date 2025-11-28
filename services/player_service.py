"""
玩家服务层
处理玩家相关的业务逻辑
"""
from services.base_service import BaseService
from database.dao.player_dao import PlayerDAO
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class PlayerService(BaseService):
    """玩家服务层"""

    def __init__(self):
        super().__init__()
        self.player_dao = self.dao_manager.player

    def create_player(self, name: str, password: str = "default") -> int:
        """创建新玩家"""
        self.validate_string(name, "玩家名")
        self.validate_string(password, "密码")

        try:
            self.log_operation(f"创建玩家: {name}")
            return self.player_dao.save_player(name, password)
        except Exception as e:
            self.handle_error(e, "创建玩家")

    def get_player(self, player_id: int) -> Optional[Dict[str, Any]]:
        """获取玩家信息"""
        self.validate_id(player_id, "玩家ID")

        try:
            return self.player_dao.get_by_id(player_id)
        except Exception as e:
            self.handle_error(e, "获取玩家信息")

    def get_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """根据ID获取玩家信息（别名方法）"""
        return self.get_player(player_id)

    def update_player_stats(self, player_id: int, stats: Dict[str, int]) -> bool:
        """更新玩家状态"""
        self.validate_id(player_id, "玩家ID")

        for stat_name, value in stats.items():
            self.validate_non_negative(value, f"{stat_name}值")

        try:
            self.log_operation(f"更新玩家状态: 玩家{player_id}")
            return self.player_dao.update_player_stats(player_id, stats)
        except Exception as e:
            self.handle_error(e, "更新玩家状态")

    def update_player_position(self, player_id: int, x: int, y: int, floor_level: int) -> bool:
        """更新玩家位置"""
        self.validate_id(player_id, "玩家ID")
        self.validate_non_negative(x, "X坐标")
        self.validate_non_negative(y, "Y坐标")
        self.validate_non_negative(floor_level, "楼层")

        try:
            self.log_operation(f"更新玩家位置: 玩家{player_id}到{floor_level}层({x},{y})")
            return self.player_dao.update_position(player_id, x, y, floor_level)
        except Exception as e:
            self.handle_error(e, "更新玩家位置")

    def add_gold(self, player_id: int, amount: int) -> bool:
        """增加玩家金币"""
        self.validate_id(player_id, "玩家ID")
        self.validate_non_negative(amount, "金币数量")

        if amount <= 0:
            return False

        try:
            self.log_operation(f"增加金币: 玩家{player_id}+{amount}金币")
            return self.player_dao.add_gold(player_id, amount)
        except Exception as e:
            self.handle_error(e, "增加金币")

    def subtract_gold(self, player_id: int, amount: int) -> bool:
        """扣除玩家金币"""
        self.validate_id(player_id, "玩家ID")
        self.validate_non_negative(amount, "金币数量")

        if amount <= 0:
            return False

        try:
            self.log_operation(f"扣除金币: 玩家{player_id}-{amount}金币")
            return self.player_dao.subtract_gold(player_id, amount)
        except Exception as e:
            self.handle_error(e, "扣除金币")

    def player_level_up(self, player_id: int) -> bool:
        """玩家升级"""
        self.validate_id(player_id, "玩家ID")

        try:
            player = self.get_player(player_id)
            if not player:
                raise ValueError("玩家不存在")

            self.log_operation(f"玩家升级: {player['name']} 等级{player['level']}+1")
            return self.player_dao.level_up(player_id)
        except Exception as e:
            self.handle_error(e, "玩家升级")

    def heal_player(self, player_id: int, heal_amount: int = None) -> bool:
        """治疗玩家"""
        self.validate_id(player_id, "玩家ID")

        if heal_amount is not None:
            self.validate_non_negative(heal_amount, "治疗量")

        try:
            if heal_amount is None:
                self.log_operation(f"玩家完全治疗: 玩家{player_id}")
                return self.player_dao.heal_player(player_id)
            else:
                self.log_operation(f"玩家治疗: 玩家{player_id}+{heal_amount}血量")
                return self.player_dao.heal_player(player_id, heal_amount)
        except Exception as e:
            self.handle_error(e, "治疗玩家")

    def restore_mana(self, player_id: int, mana_amount: int = None) -> bool:
        """恢复玩家法力"""
        self.validate_id(player_id, "玩家ID")

        if mana_amount is not None:
            self.validate_non_negative(mana_amount, "法力恢复量")

        try:
            if mana_amount is None:
                self.log_operation(f"玩家完全恢复法力: 玩家{player_id}")
                return self.player_dao.restore_mana(player_id)
            else:
                self.log_operation(f"玩家恢复法力: 玩家{player_id}+{mana_amount}法力")
                return self.player_dao.restore_mana(player_id, mana_amount)
        except Exception as e:
            self.handle_error(e, "恢复玩家法力")

    def add_experience(self, player_id: int, exp_amount: int) -> bool:
        """增加玩家经验"""
        self.validate_id(player_id, "玩家ID")
        self.validate_non_negative(exp_amount, "经验值")

        if exp_amount <= 0:
            return False

        try:
            self.log_operation(f"增加经验: 玩家{player_id}+{exp_amount}经验")
            return self.player_dao.add_experience(player_id, exp_amount)
        except Exception as e:
            self.handle_error(e, "增加经验")

    def get_all_players(self) -> List[Dict[str, Any]]:
        """获取所有玩家"""
        try:
            return self.player_dao.get_all_players()
        except Exception as e:
            self.handle_error(e, "获取所有玩家")

    def update_player(self, player_id: int, update_data: Dict[str, Any]) -> bool:
        """更新玩家信息"""
        self.validate_id(player_id, "玩家ID")
        if not isinstance(update_data, dict) or not update_data:
            raise ValueError("更新数据必须是非空字典")

        try:
            self.log_operation(f"更新玩家信息: 玩家{player_id}")
            return self.player_dao.update(player_id, update_data)
        except Exception as e:
            self.handle_error(e, "更新玩家信息")

    def delete_player(self, player_id: int) -> bool:
        """删除玩家"""
        self.validate_id(player_id, "玩家ID")

        try:
            player = self.get_player(player_id)
            if not player:
                raise ValueError("玩家不存在")

            self.log_operation(f"删除玩家: {player['name']}")
            return self.player_dao.delete(player_id)
        except Exception as e:
            self.handle_error(e, "删除玩家")

    def search_players_by_name(self, name: str) -> List[Dict[str, Any]]:
        """按名称搜索玩家"""
        self.validate_string(name, "玩家名")

        try:
            self.log_operation(f"搜索玩家: {name}")
            return self.player_dao.get_players_by_name(name)
        except Exception as e:
            self.handle_error(e, "搜索玩家")

    def get_active_players(self) -> List[Dict[str, Any]]:
        """获取活跃玩家"""
        try:
            return self.player_dao.get_active_players()
        except Exception as e:
            self.handle_error(e, "获取活跃玩家")
