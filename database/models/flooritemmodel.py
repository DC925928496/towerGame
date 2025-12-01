"""
自动生成的实体类文件
生���时间: 2025-11-30 09:54:37
工具版本: 2.0.0
数据库版本: tower_game v2.2
警告: 此文件由工具自动生成，请勿手动修改！
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from datetime import date
from datetime import time

from .base_model import BaseModel

@dataclass
class FloorItemModel(BaseModel):
    """楼层物品表"""


    item_name: str

    effect_type: str

    created_at: datetime

    updated_at: datetime

    id: int = 0
    floor_id: int = 0
    item_type: str = "item"
    symbol: str = "+"
    effect_value: int = 0
    position_x: int = 0
    position_y: int = 0
    rarity_level: str = "common"
    # 外键关系
    floor: Optional['SavedFloorModel'] = None

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
        if self.floor_id is None or (isinstance(self.floor_id, str) and self.floor_id.strip() == ''):
            errors.append("所属楼层ID不能为空")
        if self.item_name is None or (isinstance(self.item_name, str) and self.item_name.strip() == ''):
            errors.append("物品名称不能为空")
        return errors

    def _validate_field_types(self) -> List[str]:
        """验证字段类型"""
        errors = []
        # id 类型验证
        if self.id is not None:
            if not isinstance(self.id, int) or isinstance(self.id, bool):
                errors.append("物品唯一标识ID必须是整数")
        # floor_id 类型验证
        if self.floor_id is not None:
            if not isinstance(self.floor_id, int) or isinstance(self.floor_id, bool):
                errors.append("所属楼层ID必须是整数")
        # item_type 类型验证
        if self.item_type is not None:
            if not isinstance(self.item_type, str):
                errors.append("物品类型(item/potion)必须是字符串")
        # item_name 类型验证
        if self.item_name is not None:
            if not isinstance(self.item_name, str):
                errors.append("物品名称必须是字符串")
        # symbol 类型验证
        if self.symbol is not None:
            if not isinstance(self.symbol, str):
                errors.append("物品显示符号必须是字符串")
        # effect_type 类型验证
        if self.effect_type is not None:
            if not isinstance(self.effect_type, str):
                errors.append("效果类型(heal/mana等)必须是字符串")
        # effect_value 类型验证
        if self.effect_value is not None:
            if not isinstance(self.effect_value, int) or isinstance(self.effect_value, bool):
                errors.append("效果数值必须是整数")
        # position_x 类型验证
        if self.position_x is not None:
            if not isinstance(self.position_x, int) or isinstance(self.position_x, bool):
                errors.append("物品X坐标必须是整数")
        # position_y 类型验证
        if self.position_y is not None:
            if not isinstance(self.position_y, int) or isinstance(self.position_y, bool):
                errors.append("物品Y坐标必须是整数")
        # rarity_level 类型验证
        if self.rarity_level is not None:
            if not isinstance(self.rarity_level, str):
                errors.append("稀有度等级必须是字符串")
        # created_at 类型验证
        if self.created_at is not None:
            if not isinstance(self.created_at, datetime):
                errors.append("物品创建时间必须是日期时间对象")
        # updated_at 类型验证
        if self.updated_at is not None:
            if not isinstance(self.updated_at, datetime):
                errors.append("物品更新时间必须是日期时间对象")
        return errors

    def _validate_field_constraints(self) -> List[str]:
        """验证字段约束"""
        errors = []
        # id 约束验证
        if self.id is not None:
            # 数值范围检查
            if self.id < 0:
                errors.append("物品唯一标识ID不能为负数")
        # floor_id 约束验证
        if self.floor_id is not None:
            # ID字段必须是正整数
            if self.floor_id <= 0:
                errors.append("所属楼层ID必须是正整数")
        # item_type 约束验证
        if self.item_type is not None:
            # 字符串长度检查
            if len(self.item_type) > 50:
                errors.append("物品类型(item/potion)长度不能超过50个字符")
        # item_name 约束验证
        if self.item_name is not None:
            # 字符串长度检查
            if len(self.item_name) > 100:
                errors.append("物品名称长度不能超过100个字符")
        # symbol 约束验证
        if self.symbol is not None:
            # 字符串长度检查
            if len(self.symbol) > 10:
                errors.append("物品显示符号长度不能超过10个字符")
        # effect_type 约束验证
        if self.effect_type is not None:
            # 字符串长度检查
            if len(self.effect_type) > 50:
                errors.append("效果类型(heal/mana等)长度不能超过50个字符")
        # effect_value 约束验证
        if self.effect_value is not None:
            # 数值范围检查
            if self.effect_value < 0:
                errors.append("效果数值不能为负数")
        # position_x 约束验证
        if self.position_x is not None:
            # 数值范围检查
            if self.position_x < 0:
                errors.append("物品X坐标不能为负数")
        # position_y 约束验证
        if self.position_y is not None:
            # 数值范围检查
            if self.position_y < 0:
                errors.append("物品Y坐标不能为负数")
        # rarity_level 约束验证
        if self.rarity_level is not None:
            # 字符串长度检查
            if len(self.rarity_level) > 20:
                errors.append("稀有度等级长度不能超过20个字符")
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
        # floor 外键验证
        if self.floor_id is not None:
            if self.floor_id <= 0:
                errors.append("floor的ID必须是有效正整数")
            if self.floor is None:
                errors.append("floor对象不存在")
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
            'valid': len(errors) == 0,
            'error_count': len(errors),
            'errors': errors,
            'field_count': 12,
            'required_fields': ['floor_id','item_name',],
            'foreign_keys': ['floor',]
        }

    def to_dict(self, exclude_none: bool = False) -> Dict[str, Any]:
        """
        转换为字典

        Args:
            exclude_none: 是否排除None值

        Returns:
            字典表示
        """
        result = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

        if exclude_none:
            result = {k: v for k, v in result.items() if v is not None}

        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FloorItemModel':
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
        # floor_id 数据清理
        if self.floor_id is not None:
            try:
                self.floor_id = int(self.floor_id)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # item_type 数据清理
        if self.item_type:
            # 去除首尾空格
            self.item_type = self.item_type.strip()
        # item_name 数据清理
        if self.item_name:
            # 去除首尾空格
            self.item_name = self.item_name.strip()
        # symbol 数据清理
        if self.symbol:
            # 去除首尾空格
            self.symbol = self.symbol.strip()
        # effect_type 数据清理
        if self.effect_type:
            # 去除首尾空格
            self.effect_type = self.effect_type.strip()
        # effect_value 数据清理
        if self.effect_value is not None:
            try:
                self.effect_value = int(self.effect_value)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # position_x 数据清理
        if self.position_x is not None:
            try:
                self.position_x = int(self.position_x)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # position_y 数据清理
        if self.position_y is not None:
            try:
                self.position_y = int(self.position_y)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # rarity_level 数据清理
        if self.rarity_level:
            # 去除首尾空格
            self.rarity_level = self.rarity_level.strip()
        # created_at 数据清理
        # updated_at 数据清理
