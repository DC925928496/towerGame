"""
自动生成的实体类文件
生���时间: 2025-12-09 13:33:33
工具版本: 2.0.0
数据库版本: tower_game v2.2
警告: 此文件由工具自动生成，请勿手动修改！
"""

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Dict, List, Optional

from .base_model import BaseModel


@dataclass
class SavedFloorModel(BaseModel):
    """保存的楼层表"""

    created_at: datetime

    updated_at: datetime

    id: int = 0
    save_id: int = 0
    player_id: int = 0
    floor_level: int = 0
    width: int = 15
    height: int = 15
    player_start_x: int = 7
    player_start_y: int = 7
    stairs_x: int = 0
    stairs_y: int = 0
    is_merchant_floor: int = 0

    # 用户自定义方法保护区域
    # === USER_CUSTOM_METHODS_START ===
    # 用户可以在这里添加自定义方法，此区域不会被覆盖
    # === USER_CUSTOM_METHODS_END ===

    def validate(self, skip_foreign_keys: bool = False) -> List[str]:
        """
        增强的字段验证逻辑

        Args:
            skip_foreign_keys: 是否跳过外键验证

        Returns:
            验证错误列表
        """
        errors = []

        # 基本字段验证
        errors.extend(self._validate_required_fields())
        errors.extend(self._validate_field_types())
        errors.extend(self._validate_field_constraints())

        # 外键验证
        if not skip_foreign_keys:
            errors.extend(self._validate_foreign_keys())

        # 自定义业务验证
        errors.extend(self._validate_business_rules())

        return errors

    def _validate_required_fields(self) -> List[str]:
        """验证必填字段"""
        errors = []
        if self.save_id is None or (
            isinstance(self.save_id, str) and self.save_id.strip() == ""
        ):
            errors.append("所属存档ID不能为空")
        if self.player_id is None or (
            isinstance(self.player_id, str) and self.player_id.strip() == ""
        ):
            errors.append("player_id不能为空")
        if self.floor_level is None or (
            isinstance(self.floor_level, str) and self.floor_level.strip() == ""
        ):
            errors.append("楼层编号不能为空")
        return errors

    def _validate_field_types(self) -> List[str]:
        """验证字段类型"""
        errors = []
        # id 类型验证
        if self.id is not None:
            if not isinstance(self.id, int) or isinstance(self.id, bool):
                errors.append("楼层唯一标识ID必须是整数")
        # save_id 类型验证
        if self.save_id is not None:
            if not isinstance(self.save_id, int) or isinstance(self.save_id, bool):
                errors.append("所属存档ID必须是整数")
        # player_id 类型验证
        if self.player_id is not None:
            if not isinstance(self.player_id, int) or isinstance(self.player_id, bool):
                errors.append("player_id必须是整数")
        # floor_level 类型验证
        if self.floor_level is not None:
            if not isinstance(self.floor_level, int) or isinstance(
                self.floor_level, bool
            ):
                errors.append("楼层编号必须是整数")
        # width 类型验证
        if self.width is not None:
            if not isinstance(self.width, int) or isinstance(self.width, bool):
                errors.append("楼层宽度必须是整数")
        # height 类型验证
        if self.height is not None:
            if not isinstance(self.height, int) or isinstance(self.height, bool):
                errors.append("楼层高度必须是整数")
        # player_start_x 类型验证
        if self.player_start_x is not None:
            if not isinstance(self.player_start_x, int) or isinstance(
                self.player_start_x, bool
            ):
                errors.append("玩家起始X坐标必须是整数")
        # player_start_y 类型验证
        if self.player_start_y is not None:
            if not isinstance(self.player_start_y, int) or isinstance(
                self.player_start_y, bool
            ):
                errors.append("玩家起始Y坐标必须是整数")
        # stairs_x 类型验证
        if self.stairs_x is not None:
            if not isinstance(self.stairs_x, int) or isinstance(self.stairs_x, bool):
                errors.append("楼梯X坐标必须是整数")
        # stairs_y 类型验证
        if self.stairs_y is not None:
            if not isinstance(self.stairs_y, int) or isinstance(self.stairs_y, bool):
                errors.append("楼梯Y坐标必须是整数")
        # is_merchant_floor 类型验证
        if self.is_merchant_floor is not None:
            if not isinstance(self.is_merchant_floor, int) or isinstance(
                self.is_merchant_floor, bool
            ):
                errors.append("是否为商人楼层必须是整数")
        # created_at 类型验证
        if self.created_at is not None:
            if not isinstance(self.created_at, datetime):
                errors.append("楼层创建时间必须是日期时间对象")
        # updated_at 类型验证
        if self.updated_at is not None:
            if not isinstance(self.updated_at, datetime):
                errors.append("楼层更新时间必须是日期时间对象")
        return errors

    def _validate_field_constraints(self) -> List[str]:
        """验证字段约束"""
        errors = []
        # id 约束验证
        if self.id is not None:
            # 数值范围检查
            if self.id < 0:
                errors.append("楼层唯一标识ID不能为负数")
        # save_id 约束验证
        if self.save_id is not None:
            # ID字段必须是正整数
            if self.save_id <= 0:
                errors.append("所属存档ID必须是正整数")
        # player_id 约束验证
        if self.player_id is not None:
            # ID字段必须是正整数
            if self.player_id <= 0:
                errors.append("player_id必须是正整数")
        # floor_level 约束验证
        if self.floor_level is not None:
            # 数值范围检查
            if self.floor_level < 0:
                errors.append("楼层编号不能为负数")
        # width 约束验证
        if self.width is not None:
            # 数值范围检查
            if self.width < 0:
                errors.append("楼层宽度不能为负数")
        # height 约束验证
        if self.height is not None:
            # 数值范围检查
            if self.height < 0:
                errors.append("楼层高度不能为负数")
        # player_start_x 约束验证
        if self.player_start_x is not None:
            # 数值范围检查
            if self.player_start_x < 0:
                errors.append("玩家起始X坐标不能为负数")
        # player_start_y 约束验证
        if self.player_start_y is not None:
            # 数值范围检查
            if self.player_start_y < 0:
                errors.append("玩家起始Y坐标不能为负数")
        # stairs_x 约束验证
        if self.stairs_x is not None:
            # 数值范围检查
            if self.stairs_x < 0:
                errors.append("楼梯X坐标不能为负数")
        # stairs_y 约束验证
        if self.stairs_y is not None:
            # 数值范围检查
            if self.stairs_y < 0:
                errors.append("楼梯Y坐标不能为负数")
        # is_merchant_floor 约束验证
        if self.is_merchant_floor is not None:
            # 数值范围检查
            if self.is_merchant_floor < 0:
                errors.append("是否为商人楼层不能为负数")
        # created_at 约束验证
        if self.created_at is not None:
            # datetime类型不需要长度验证
            pass
        # updated_at 约束验证
        if self.updated_at is not None:
            # datetime类型不需要长度验证
            pass
        return errors

    def _validate_foreign_keys(self) -> List[str]:
        """验证外键关系"""
        errors = []
        return errors

    def _validate_business_rules(self) -> List[str]:
        """自定义业务规则验证"""
        errors = []
        # 子类可以重写此方法添加自定义业务验证逻辑

        # 通用业务规则示例：

        return errors

    def is_valid(self, skip_foreign_keys: bool = False) -> bool:
        """
        快速验证方法

        Args:
            skip_foreign_keys: 是否跳过外键验证

        Returns:
            是否验证通过
        """
        return len(self.validate(skip_foreign_keys=skip_foreign_keys)) == 0

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        获取验证摘要信息

        Returns:
            包含验证结果详细信息的字典
        """
        errors = self.validate()
        return {
            "valid": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors,
            "field_count": 13,
            "required_fields": [
                "save_id",
                "player_id",
                "floor_level",
            ],
            "foreign_keys": [],
        }

    def to_dict(self, exclude_none: bool = False) -> Dict[str, Any]:
        """
        转换为字典

        Args:
            exclude_none: 是否排除None值

        Returns:
            字典表示
        """
        result = {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

        if exclude_none:
            result = {k: v for k, v in result.items() if v is not None}

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SavedFloorModel":
        """
        从字典创建实例

        Args:
            data: 字典数据

        Returns:
            实例对象
        """
        # 过滤掉不存在的字段
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        return cls(**filtered_data)

    def __post_init__(self):
        """初始化后处理"""
        # 数据清理和标准化
        self._clean_data()

        # 基本验证（可选）
        # if not self.is_valid():
        #     raise ValueError("Invalid data detected in __post_init__")

    def _clean_data(self):
        """数据清理和标准化"""
        # id 数据清理
        if self.id is not None:
            try:
                self.id = int(self.id)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # save_id 数据清理
        if self.save_id is not None:
            try:
                self.save_id = int(self.save_id)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # player_id 数据清理
        if self.player_id is not None:
            try:
                self.player_id = int(self.player_id)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # floor_level 数据清理
        if self.floor_level is not None:
            try:
                self.floor_level = int(self.floor_level)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # width 数据清理
        if self.width is not None:
            try:
                self.width = int(self.width)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # height 数据清理
        if self.height is not None:
            try:
                self.height = int(self.height)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # player_start_x 数据清理
        if self.player_start_x is not None:
            try:
                self.player_start_x = int(self.player_start_x)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # player_start_y 数据清理
        if self.player_start_y is not None:
            try:
                self.player_start_y = int(self.player_start_y)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # stairs_x 数据清理
        if self.stairs_x is not None:
            try:
                self.stairs_x = int(self.stairs_x)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # stairs_y 数据清理
        if self.stairs_y is not None:
            try:
                self.stairs_y = int(self.stairs_y)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # is_merchant_floor 数据清理
        if self.is_merchant_floor is not None:
            try:
                self.is_merchant_floor = int(self.is_merchant_floor)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # created_at 数据清理
        # updated_at 数据清理
