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
class PlayerModel(BaseModel):
    """玩家基本信息表"""


    name: str

    created_at: datetime

    updated_at: datetime

    id: int = 0
    nickname: str = "gamer"
    password_hash: str = None
    salt: str = None
    gold: int = 0
    attack: int = 10
    defense: int = 5
    level: int = 1
    exp: int = 0
    weapon_name: str = None
    weapon_atk: int = 0
    armor_name: str = None
    armor_def: int = 0
    weapon_rarity: str = None
    position_x: int = 0
    position_y: int = 0
    floor_level: int = 1
    hp: int = 500
    max_hp: int = 500
    is_active: int = 1
    last_login: Optional[datetime] = None
    login_attempts: Optional[int] = 0
    locked_until: Optional[datetime] = None

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
        if self.name is None or (isinstance(self.name, str) and self.name.strip() == ''):
            errors.append("玩家名称，必须唯一不能为空")
        return errors

    def _validate_field_types(self) -> List[str]:
        """验证字段类型"""
        errors = []
        # id 类型验证
        if self.id is not None:
            if not isinstance(self.id, int) or isinstance(self.id, bool):
                errors.append("玩家唯一标识ID必须是整数")
        # name 类型验证
        if self.name is not None:
            if not isinstance(self.name, str):
                errors.append("玩家名称，必须唯一必须是字符串")
        # nickname 类型验证
        if self.nickname is not None:
            if not isinstance(self.nickname, str):
                errors.append("nickname必须是字符串")
        # password_hash 类型验证
        if self.password_hash is not None:
            if not isinstance(self.password_hash, str):
                errors.append("password_hash必须是字符串")
        # salt 类型验证
        if self.salt is not None:
            if not isinstance(self.salt, str):
                errors.append("salt必须是字符串")
        # gold 类型验证
        if self.gold is not None:
            if not isinstance(self.gold, int) or isinstance(self.gold, bool):
                errors.append("玩家持有金币数量必须是整数")
        # attack 类型验证
        if self.attack is not None:
            if not isinstance(self.attack, int) or isinstance(self.attack, bool):
                errors.append("玩家基础攻击力必须是整数")
        # defense 类型验证
        if self.defense is not None:
            if not isinstance(self.defense, int) or isinstance(self.defense, bool):
                errors.append("玩家基础防御力必须是整数")
        # level 类型验证
        if self.level is not None:
            if not isinstance(self.level, int) or isinstance(self.level, bool):
                errors.append("玩家等级必须是整数")
        # exp 类型验证
        if self.exp is not None:
            if not isinstance(self.exp, int) or isinstance(self.exp, bool):
                errors.append("exp必须是整数")
        # weapon_name 类型验证
        if self.weapon_name is not None:
            if not isinstance(self.weapon_name, str):
                errors.append("weapon_name必须是字符串")
        # weapon_atk 类型验证
        if self.weapon_atk is not None:
            if not isinstance(self.weapon_atk, int) or isinstance(self.weapon_atk, bool):
                errors.append("weapon_atk必须是整数")
        # armor_name 类型验证
        if self.armor_name is not None:
            if not isinstance(self.armor_name, str):
                errors.append("armor_name必须是字符串")
        # armor_def 类型验证
        if self.armor_def is not None:
            if not isinstance(self.armor_def, int) or isinstance(self.armor_def, bool):
                errors.append("armor_def必须是整数")
        # weapon_rarity 类型验证
        if self.weapon_rarity is not None:
            if not isinstance(self.weapon_rarity, str):
                errors.append("weapon_rarity必须是字符串")
        # position_x 类型验证
        if self.position_x is not None:
            if not isinstance(self.position_x, int) or isinstance(self.position_x, bool):
                errors.append("玩家在楼层中的X坐标必须是整数")
        # position_y 类型验证
        if self.position_y is not None:
            if not isinstance(self.position_y, int) or isinstance(self.position_y, bool):
                errors.append("玩家在楼层中的Y坐标必须是整数")
        # floor_level 类型验证
        if self.floor_level is not None:
            if not isinstance(self.floor_level, int) or isinstance(self.floor_level, bool):
                errors.append("玩家所在楼层必须是整数")
        # hp 类型验证
        if self.hp is not None:
            if not isinstance(self.hp, int) or isinstance(self.hp, bool):
                errors.append("hp必须是整数")
        # max_hp 类型验证
        if self.max_hp is not None:
            if not isinstance(self.max_hp, int) or isinstance(self.max_hp, bool):
                errors.append("max_hp必须是整数")
        # is_active 类型验证
        if self.is_active is not None:
            if not isinstance(self.is_active, int) or isinstance(self.is_active, bool):
                errors.append("玩家是否处于活跃状态必须是整数")
        # created_at 类型验证
        if self.created_at is not None:
            if not isinstance(self.created_at, datetime):
                errors.append("玩家创建时间必须是日期时间对象")
        # updated_at 类型验证
        if self.updated_at is not None:
            if not isinstance(self.updated_at, datetime):
                errors.append("玩家信息最后更新时间必须是日期时间对象")
        # last_login 类型验证
        if self.last_login is not None:
            if not isinstance(self.last_login, datetime):
                errors.append("最后登录时间必须是日期时间对象")
        # login_attempts 类型验证
        if self.login_attempts is not None:
            if not isinstance(self.login_attempts, int) or isinstance(self.login_attempts, bool):
                errors.append("登录失败次数必须是整数")
        # locked_until 类型验证
        if self.locked_until is not None:
            if not isinstance(self.locked_until, datetime):
                errors.append("锁定到期时间必须是日期时间对象")
        return errors

    def _validate_field_constraints(self) -> List[str]:
        """验证字段约束"""
        errors = []
        # id 约束验证
        if self.id is not None:
            # 数值范围检查
            if self.id < 0:
                errors.append("玩家唯一标识ID不能为负数")
        # name 约束验证
        if self.name is not None:
            # 字符串长度检查
            if len(self.name) > 100:
                errors.append("玩家名称，必须唯一长度不能超过100个字符")
        # nickname 约束验证
        if self.nickname is not None:
            # 字符串长度检查
            if len(self.nickname) > 50:
                errors.append("nickname长度不能超过50个字符")
        # password_hash 约束验证
        if self.password_hash is not None:
            # 字符串长度检查
            if len(self.password_hash) > 255:
                errors.append("password_hash长度不能超过255个字符")
        # salt 约束验证
        if self.salt is not None:
            # 字符串长度检查
            if len(self.salt) > 32:
                errors.append("salt长度不能超过32个字符")
        # gold 约束验证
        if self.gold is not None:
            # 数值范围检查
            if self.gold < 0:
                errors.append("玩家持有金币数量不能为负数")
        # attack 约束验证
        if self.attack is not None:
            # 数值范围检查
            if self.attack < 0:
                errors.append("玩家基础攻击力不能为负数")
        # defense 约束验证
        if self.defense is not None:
            # 数值范围检查
            if self.defense < 0:
                errors.append("玩家基础防御力不能为负数")
        # level 约束验证
        if self.level is not None:
            # 数值范围检查
            if self.level < 0:
                errors.append("玩家等级不能为负数")
        # exp 约束验证
        if self.exp is not None:
            # 数值范围检查
            if self.exp < 0:
                errors.append("exp不能为负数")
        # weapon_name 约束验证
        if self.weapon_name is not None:
            # 字符串长度检查
            if len(self.weapon_name) > 120:
                errors.append("weapon_name长度不能超过120个字符")
        # weapon_atk 约束验证
        if self.weapon_atk is not None:
            # 数值范围检查
            if self.weapon_atk < 0:
                errors.append("weapon_atk不能为负数")
        # armor_name 约束验证
        if self.armor_name is not None:
            # 字符串长度检查
            if len(self.armor_name) > 120:
                errors.append("armor_name长度不能超过120个字符")
        # armor_def 约束验证
        if self.armor_def is not None:
            # 数值范围检查
            if self.armor_def < 0:
                errors.append("armor_def不能为负数")
        # weapon_rarity 约束验证
        if self.weapon_rarity is not None:
            # 字符串长度检查
            if len(self.weapon_rarity) > 20:
                errors.append("weapon_rarity长度不能超过20个字符")
        # position_x 约束验证
        if self.position_x is not None:
            # 数值范围检查
            if self.position_x < 0:
                errors.append("玩家在楼层中的X坐标不能为负数")
        # position_y 约束验证
        if self.position_y is not None:
            # 数值范围检查
            if self.position_y < 0:
                errors.append("玩家在楼层中的Y坐标不能为负数")
        # floor_level 约束验证
        if self.floor_level is not None:
            # 数值范围检查
            if self.floor_level < 0:
                errors.append("玩家所在楼层不能为负数")
        # hp 约束验证
        if self.hp is not None:
            # 数值范围检查
            if self.hp < 0:
                errors.append("hp不能为负数")
        # max_hp 约束验证
        if self.max_hp is not None:
            # 数值范围检查
            if self.max_hp < 0:
                errors.append("max_hp不能为负数")
        # is_active 约束验证
        if self.is_active is not None:
            # 数值范围检查
            if self.is_active < 0:
                errors.append("玩家是否处于活跃状态不能为负数")
        # created_at 约束验证
        if self.created_at is not None:
            # datetime类型不需要长度验证
            pass
        # updated_at 约束验证
        if self.updated_at is not None:
            # datetime类型不需要长度验证
            pass
        # last_login 约束验证
        if self.last_login is not None:
            # datetime类型不需要范围验证
            pass
        # login_attempts 约束验证
        if self.login_attempts is not None:
            if self.login_attempts < 0:
                errors.append("登录失败次数不能为负数")
        # locked_until 约束验证
        if self.locked_until is not None:
            # datetime类型不需要范围验证
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
            'valid': len(errors) == 0,
            'error_count': len(errors),
            'errors': errors,
            'field_count': 26,
            'required_fields': ['name',],
            'foreign_keys': []
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
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerModel':
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
        # name 数据清理
        if self.name:
            # 去除首尾空格
            self.name = self.name.strip()
        # nickname 数据清理
        if self.nickname:
            # 去除首尾空格
            self.nickname = self.nickname.strip()
        # password_hash 数据清理
        if self.password_hash:
            # 去除首尾空格
            self.password_hash = self.password_hash.strip()
        # salt 数据清理
        if self.salt:
            # 去除首尾空格
            self.salt = self.salt.strip()
        # gold 数据清理
        if self.gold is not None:
            try:
                self.gold = int(self.gold)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # attack 数据清理
        if self.attack is not None:
            try:
                self.attack = int(self.attack)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # defense 数据清理
        if self.defense is not None:
            try:
                self.defense = int(self.defense)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # level 数据清理
        if self.level is not None:
            try:
                self.level = int(self.level)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # exp 数据清理
        if self.exp is not None:
            try:
                self.exp = int(self.exp)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # weapon_name 数据清理
        if self.weapon_name:
            # 去除首尾空格
            self.weapon_name = self.weapon_name.strip()
        # weapon_atk 数据清理
        if self.weapon_atk is not None:
            try:
                self.weapon_atk = int(self.weapon_atk)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # armor_name 数据清理
        if self.armor_name:
            # 去除首尾空格
            self.armor_name = self.armor_name.strip()
        # armor_def 数据清理
        if self.armor_def is not None:
            try:
                self.armor_def = int(self.armor_def)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # weapon_rarity 数据清理
        if self.weapon_rarity:
            # 去除首尾空格
            self.weapon_rarity = self.weapon_rarity.strip()
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
        # floor_level 数据清理
        if self.floor_level is not None:
            try:
                self.floor_level = int(self.floor_level)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # hp 数据清理
        if self.hp is not None:
            try:
                self.hp = int(self.hp)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # max_hp 数据清理
        if self.max_hp is not None:
            try:
                self.max_hp = int(self.max_hp)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # is_active 数据清理
        if self.is_active is not None:
            try:
                self.is_active = int(self.is_active)
            except (ValueError, TypeError):
                pass  # 保持原值，在validate中会报错
        # created_at 数据清理
        # updated_at 数据清理
        # last_login 数据清理
        # login_attempts 数据清理
        # locked_until 数据清理
