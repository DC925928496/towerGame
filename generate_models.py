#!/usr/bin/env python3
"""
数据库实体类自动生成工具 - 主入口脚本

使用方法:
  python generate_models.py generate --all          # 生成所有表的实体类
  python generate_models.py generate -t table_name   # 生成指定表的实体类
  python generate_models.py preview -t table_name    # 预览生成代码
  python generate_models.py list-tables              # 列出所有表
  python generate_models.py test-connection          # 测试数据库连接
  python generate_models.py --help                   # 显示帮助
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from tools.database_codegen.cli import cli
import tools.database_codegen as codegen

def main():
    """主入口函数"""
    try:
        # 显示工具信息
        print(f"数据库实体类自动生成工具 v{codegen.__version__}")
        print(f"作者: {codegen.__author__}")
        print()

        # 调用CLI
        cli()

    except KeyboardInterrupt:
        print("\n操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"程序执行出错: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()