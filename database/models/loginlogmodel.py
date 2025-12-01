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
class LoginLogModel(BaseModel):
    """用户登录日志表"""


    login_type: str

    created_at: datetime

    id: int = 0
    player_id: Optional[int] = None
    username: str = None
    ip_address: str = None
    user_agent: str = None
    reason: str = None
    # 外键关系
    player: Optional['PlayerModel'] = None

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
        if self.login_type is None or (isinstance(self.login_type, str) and self.login_type.strip() == ''):
            errors.append("登录类型不能为空")
        return errors

    def _validate_field_types(self) -> List[str]:
        """验证字段类型"""
        errors = []
        # id 类型验证
        if self.id is not None:
            if not isinstance(self.id, int) or isinstance(self.id, bool):
                errors.append("日志唯一标识ID必须是整数")
        # player_id 类型验证
        if self.player_id is not None:
            if not isinstance(self.player_id, int) or isinstance(self.player_id, bool):
                errors.append("玩家ID必须是整数")
        # username 类型验证
        if self.username is not None:
            if not isinstance(self.username, str):
                errors.append("用户名必须是字符串")
        # ip_address 类型验证
        if self.ip_address is not None:
            if not isinstance(self.ip_address, str):
                errors.append("登录IP地址必须是字符串")
        # user_agent 类型验证
        if self.user_agent is not None:
            if not isinstance(self.user_agent, str):
                errors.append("用户代理信息必须是字符串")
        # login_type 类型验证
        if self.login_type is not None:
            if not isinstance(self.login_type, str):
                errors.append("登录类型必须是字符串")
        # reason 类型验证
        if self.reason is not None:
            if not isinstance(self.reason, str):
                errors.append("登录失败原因或其他说明必须是字符串")
        # created_at 类型验证
        if self.created_at is not None:
            if not isinstance(self.created_at, datetime):
                errors.append("日志创建时间必须是日期时间对象")
        return errors

    def _validate_field_constraints(self) -> List[str]:
        """验证字段约束"""
        errors = []
        # id 约束验证
        if self.id is not None:
            # 数值范围检查
            if self.id < 0:
                errors.append("日志唯一标识ID不能为负数")
        # player_id 约束验证
        if self.player_id is not None:
        # username 约束验证
        if self.username is not None:
            # 字符串长度检查
            if len(self.username) > 100:
                errors.append("用户名长度不能超过100个字符")
        # ip_address 约束验证
        if self.ip_address is not None:
            # 字符串长度检查
            if len(self.ip_address) > 45:
                errors.append("登录IP地址长度不能超过45个字符")
        # user_agent 约束验证
        if self.user_agent is not None:
            # 字符串长度检查
            if len(self.user_agent) > 65535:
                errors.append("用户代理信息长度不能超过65535个字符")
        # login_type 约束验证
        if self.login_type is not None:
            # 字符串长度检查
            if len(self.login_type) > 8:
                errors.append("登录类型长度不能超过8个字符")
        # reason 约束验证
        if self.reason is not None:
            # 字符串长度检查
            if len(self.reason) > 255:
                errors.append("登录失败原因或其他说明长度不能超过255个字符")
        # created_at 约束验证
        if self.created_at is not None:
            # datetime类型不需要长度验证
            pass
        return errors

    def _validate_foreign_keys(self) -> List[str]:
        """验证外键关系"""
        errors = []
        # player 外键验证
        if self.player_id is not None:
            if self.player_id <= 0:
                errors.append("player的ID必须是有效正整数")
            if self.player is None:
                errors.append("player对象不存在")
        return errors

    def _validate_business_rules(self) -> List[str]:
        """自定义业务规则验证"""
        errors = []
        # 子类可以重写此方法添加自定义业务验证逻辑

        # 通用业务规则示例：
        # 用户名格式检查
        if self.username:
            import re
            if not re.match(r'^[a-zA-Z0-9_]{3,20}$', self.username):
                errors.append("用户名只能包含字母、数字和下划线，长度3-20位")

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
            'field_count': 8,
            'required_fields': ['login_type',],
            'foreign_keys': ['player',]
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
    def from_dict(cls, data: Dict[str, Any]) -> 'LoginLogModel':
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
        # player_id 数据清理
        # username 数据清理
        if self.username:
            # 去除首尾空格
            self.username = self.username.strip()
            # 转换为小写
            self.username = self.username.lower()
        # ip_address 数据清理
        if self.ip_address:
            # 去除首尾空格
            self.ip_address = self.ip_address.strip()
        # user_agent 数据清理
        if self.user_agent:
            # 去除首尾空格
            self.user_agent = self.user_agent.strip()
        # login_type 数据清理
        if self.login_type:
            # 去除首尾空格
            self.login_type = self.login_type.strip()
        # reason 数据清理
        if self.reason:
            # 去除首尾空格
            self.reason = self.reason.strip()
        # created_at 数据清理
