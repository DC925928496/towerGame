"""
游戏存档服务层
处理游戏存档相关的业务逻辑
"""
from services.base_service import BaseService
from database.dao.game_save_dao import GameSaveDAO
from database.dao.floor_dao import FloorDAO
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GameSaveService(BaseService):
    """游戏存档服务层"""

    def __init__(self):
        super().__init__()
        self.game_save_dao = self.dao_manager.game_save
        self.floor_dao = self.dao_manager.floor

    def create_save(self, player_id: int, floor_level: int, save_name: str = None) -> int:
        """创建游戏存档"""
        self.validate_id(player_id, "玩家ID")
        self.validate_non_negative(floor_level, "楼层")

        if save_name:
            self.validate_string(save_name, "存档名")

        try:
            # 停用其他存档
            self.deactivate_all_saves(player_id)

            save_id = self.game_save_dao.save_game_state(player_id, floor_level, save_name)
            self.log_operation(f"创建存档: 玩家{player_id} 楼层{floor_level}")
            return save_id
        except Exception as e:
            self.handle_error(e, "创建存档")

    def get_save(self, save_id: int) -> Optional[Dict[str, Any]]:
        """获取存档信息"""
        self.validate_id(save_id, "存档ID")

        try:
            return self.game_save_dao.get_by_id(save_id)
        except Exception as e:
            self.handle_error(e, "获取存档信息")

    def update_save(self, save_id: int, data: Dict[str, Any]) -> bool:
        """更新存档信息"""
        self.validate_id(save_id, "存档ID")

        try:
            if 'floor_level' in data:
                self.validate_non_negative(data['floor_level'], "楼层")

            if 'save_name' in data:
                self.validate_string(data['save_name'], "存档名")

            self.log_operation(f"更新存档: 存档{save_id}")
            return self.game_save_dao.update(save_id, data)
        except Exception as e:
            self.handle_error(e, "更新存档信息")

    def delete_save(self, save_id: int) -> bool:
        """删除存档"""
        self.validate_id(save_id, "存档ID")

        try:
            save = self.get_save(save_id)
            if not save:
                logger.info(f"存档{save_id}不存在，跳过删除请求")
                return False

            self.log_operation(f"删除存档: {save['save_name']}")
            return self.game_save_dao.delete(save_id)
        except Exception as e:
            self.handle_error(e, "删除存档")

    def get_player_saves(self, player_id: int) -> List[Dict[str, Any]]:
        """获取玩家的所有存档"""
        self.validate_id(player_id, "玩家ID")

        try:
            return self.game_save_dao.get_all_saves(player_id)
        except Exception as e:
            self.handle_error(e, "获取玩家存档")

    def get_all_saves(self) -> List[Dict[str, Any]]:
        """获取所有存档"""
        try:
            return self.game_save_dao.get_all_saves()
        except Exception as e:
            self.handle_error(e, "获取所有存档")

    def get_latest_save(self, player_id: int = None) -> Optional[Dict[str, Any]]:
        """获取最新存档"""
        if player_id:
            self.validate_id(player_id, "玩家ID")

        try:
            return self.game_save_dao.get_latest_save(player_id)
        except Exception as e:
            self.handle_error(e, "获取最新存档")

    def quick_save(self, player_id: int, floor_level: int) -> int:
        """快速保存"""
        self.validate_id(player_id, "玩家ID")
        self.validate_non_negative(floor_level, "楼层")

        try:
            save_name = f"快速保存_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return self.create_save(player_id, floor_level, save_name)
        except Exception as e:
            self.handle_error(e, "快速保存")

    def auto_save(self, player_id: int, floor_level: int) -> int:
        """自动保存"""
        self.validate_id(player_id, "玩家ID")
        self.validate_non_negative(floor_level, "楼层")

        try:
            save_name = f"自动保存_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            return self.create_save(player_id, floor_level, save_name)
        except Exception as e:
            self.handle_error(e, "自动保存")

    def deactivate_all_saves(self, player_id: int) -> bool:
        """停用玩家的所有存档"""
        self.validate_id(player_id, "玩家ID")

        try:
            return self.game_save_dao.deactivate_all_saves(player_id)
        except Exception as e:
            self.handle_error(e, "停用存档")

    def get_saves_by_floor_range(self, min_floor: int, max_floor: int) -> List[Dict[str, Any]]:
        """获取指定楼层范围的存档"""
        self.validate_non_negative(min_floor, "最小楼层")
        self.validate_non_negative(max_floor, "最大楼层")

        if min_floor > max_floor:
            raise ValueError("最小楼层不能大于最大楼层")

        try:
            return self.game_save_dao.get_saves_by_floor_range(min_floor, max_floor)
        except Exception as e:
            self.handle_error(e, "获取楼层范围存档")

    def get_save_count(self, player_id: int = None) -> int:
        """获取存档数量"""
        if player_id:
            self.validate_id(player_id, "玩家ID")

        try:
            return self.game_save_dao.get_save_count(player_id)
        except Exception as e:
            self.handle_error(e, "获取存档数量")

    def load_save(self, save_id: int) -> Optional[Dict[str, Any]]:
        """加载存档（游戏逻辑）"""
        self.validate_id(save_id, "存档ID")

        try:
            save_info = self.get_save(save_id)
            if not save_info:
                raise ValueError("存档不存在")

            # 获取对应的楼层数据
            floor_info = self.floor_dao.get_by_save_id(save_info['player_id'])

            self.log_operation(f"加载存档: {save_info['save_name']}")

            return {
                'save_info': save_info,
                'floor_info': floor_info
            }
        except Exception as e:
            self.handle_error(e, "加载存档")
