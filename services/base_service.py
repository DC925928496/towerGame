"""
服务层基类
提供服务层通用的操作和错误处理
"""
from database.dao import dao_manager
import logging
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class BaseService:
    """服务层基类"""

    def __init__(self):
        """初始化服务层基类"""
        self.dao_manager = dao_manager

    def handle_error(self, error: Exception, operation: str = "操作") -> None:
        """统一错误处理"""
        logger.error(f"{operation}失败: {error}")
        raise error

    def log_operation(self, operation: str, details: str = "") -> None:
        """记录操作日志"""
        if details:
            logger.info(f"{operation}: {details}")
        else:
            logger.info(f"{operation}")

    def validate_id(self, id_value: int, field_name: str = "ID") -> None:
        """验证ID参数"""
        if not isinstance(id_value, int) or id_value <= 0:
            raise ValueError(f"{field_name}必须是正整数")

    def validate_string(self, value: str, field_name: str = "字符串", min_length: int = 1) -> None:
        """验证字符串参数"""
        if not isinstance(value, str) or len(value.strip()) < min_length:
            raise ValueError(f"{field_name}必须是非空字符串")

    def validate_non_negative(self, value: Union[int, float], field_name: str = "数值") -> None:
        """验证非负数"""
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"{field_name}必须是非负数")

    def create_response(self, success: bool, data: Any = None, message: str = "", error: str = "") -> Dict[str, Any]:
        """创建统一响应格式"""
        response = {
            "success": success,
            "data": data,
            "message": message
        }
        if error:
            response["error"] = error
        return response