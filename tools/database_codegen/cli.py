"""命令行接口模块

提供命令行工具的入口点，支持各种生成和更新操作
"""

import click
import sys
import os
import logging
from pathlib import Path
from typing import List, Optional

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.database_codegen.config_manager import ConfigManager
from tools.database_codegen.entity_generator import EntityGenerator
from tools.database_codegen.metadata_reader import DatabaseMetadataReader

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.group()
@click.option('--config', '-c', help='配置文件路径')
@click.option('--verbose', '-v', is_flag=True, help='详细输出模式')
@click.pass_context
def cli(ctx, config, verbose):
    """数据库实体类自动生成工具"""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)

    # 初始化配置管理器
    try:
        config_manager = ConfigManager(config)
        ctx.ensure_object(dict)
        ctx.obj['config'] = config_manager
    except Exception as e:
        logger.error(f"Failed to initialize configuration: {e}")
        sys.exit(1)

@cli.command()
@click.option('--all', 'generate_all', is_flag=True, help='生成所有表的实体类')
@click.option('--table', '-t', help='指定表名，多个表用逗号分隔')
@click.option('--output', '-o', help='指定输出目录')
@click.option('--preview', '-p', is_flag=True, help='预览模式，不生成文件')
@click.option('--force', '-f', is_flag=True, help='强制覆盖现有文件')
@click.pass_context
def generate(ctx, generate_all, table, output, preview, force):
    """生成实体类"""
    config = ctx.obj['config']

    # 更新输出目录配置
    if output:
        config.config.generation.output_dir = output

    try:
        generator = EntityGenerator(config)

        if preview:
            logger.info("Running in preview mode - no files will be created")

        if generate_all:
            # 生成所有表
            logger.info("Generating entities for all tables")
            files = generator.generate_all_entities(preview_mode=preview)
            logger.info(f"Would generate {len(files)} entity files")

        elif table:
            # 生成指定表
            table_names = [t.strip() for t in table.split(',') if t.strip()]
            logger.info(f"Generating entities for tables: {table_names}")

            all_files = []
            for table_name in table_names:
                file_path = generator.generate_entity(table_name, preview_mode=preview)
                if file_path:
                    all_files.append(file_path)

            logger.info(f"Would generate {len(all_files)} entity files: {all_files}")

        else:
            logger.error("Please specify either --all or --table option")
            sys.exit(1)

        generator.close()

    except Exception as e:
        logger.error(f"Failed to generate entities: {e}")
        sys.exit(1)

@cli.command()
@click.option('--all', 'update_all', is_flag=True, help='更新所有表')
@click.option('--table', '-t', help='指定表名，多个表用逗号分隔')
@click.option('--backup', '-b', is_flag=True, help='备份用户自定义方法')
@click.option('--preview', '-p', is_flag=True, help='预览模式，不实际生成文件')
@click.option('--clear-cache', is_flag=True, help='清除变更缓存')
@click.pass_context
def update(ctx, update_all, table, backup, preview, clear_cache):
    """增量更新实体类"""
    config = ctx.obj['config']

    if backup:
        config.config.generation.custom_methods_protection = True

    try:
        generator = EntityGenerator(config)

        if clear_cache:
            generator.incremental_updater.clear_cache()
            logger.info("已清除变更缓存")

        if update_all:
            # 增量更新所有表
            logger.info("开始增量更新所有实体类")
            files = generator.update_all_entities_incremental(
                preview_mode=preview,
                backup_custom_methods=backup
            )
            if preview:
                logger.info(f"预览模式 - 将更新 {len(files)} 个文件")
            else:
                logger.info(f"增量更新完成，更新了 {len(files)} 个文件")

        elif table:
            # 增量更新指定表
            table_names = [t.strip() for t in table.split(',') if t.strip()]
            logger.info(f"增量更新指定表: {table_names}")

            # 对于指定表的增量更新，暂时使用生成命令
            for table_name in table_names:
                from .utils import safe_class_name
                class_name = safe_class_name(table_name) + config.config.generation.suffix
                file_name = f"{class_name.lower()}.py"
                file_path = Path(config.config.generation.output_dir) / file_name

                if preview:
                    logger.info(f"预览模式 - 将更新文件: {file_path}")
                else:
                    # 读取表元数据并更新
                    table_metadata = generator.metadata_reader.read_table_metadata(table_name)
                    if table_metadata:
                        success = generator.incremental_updater.apply_incremental_update(
                            table_metadata, file_path, backup
                        )
                        if success:
                            logger.info(f"增量更新成功: {file_path}")
                        else:
                            logger.error(f"增量更新失败: {file_path}")

        generator.close()

    except Exception as e:
        logger.error(f"增量更新失败: {e}")
        sys.exit(1)

@cli.command()
@click.option('--table', '-t', help='指定表名')
@click.pass_context
def preview(ctx, table):
    """预览生成的代码"""
    config = ctx.obj['config']

    try:
        generator = EntityGenerator(config)

        if table:
            # 预览指定表
            logger.info(f"Previewing entity for table: {table}")
            code = generator.get_preview_for_table(table)
            if code:
                print("\n" + "="*60)
                print(f"Generated code for table: {table}")
                print("="*60)
                print(code)
                print("="*60)
            else:
                logger.error(f"Failed to generate preview for table: {table}")
                sys.exit(1)
        else:
            logger.error("Please specify a table name with --table option")
            sys.exit(1)

        generator.close()

    except Exception as e:
        logger.error(f"Failed to generate preview: {e}")
        sys.exit(1)

@cli.command()
@click.pass_context
def list_tables(ctx):
    """列出所有表"""
    config = ctx.obj['config']

    try:
        reader = DatabaseMetadataReader(config)

        if not reader.test_connection():
            logger.error("Failed to connect to database")
            sys.exit(1)

        with reader.get_connection() as conn:
            tables = reader._get_table_names(conn)
        reader.close()

        logger.info(f"Found {len(tables)} tables:")
        for table in sorted(tables):
            if not config.should_exclude_table(table):
                print(f"  - {table}")
            else:
                print(f"  - {table} (excluded)")

    except Exception as e:
        logger.error(f"Failed to list tables: {e}")
        sys.exit(1)

@cli.command()
@click.pass_context
def test_connection(ctx):
    """测试数据库连接"""
    config = ctx.obj['config']

    try:
        reader = DatabaseMetadataReader(config)

        if reader.test_connection():
            logger.info("Database connection test successful")
            logger.info(f"Connected to: {config.config.database.database}@{config.config.database.host}:{config.config.database.port}")
        else:
            logger.error("Database connection test failed")
            sys.exit(1)

        reader.close()

    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        sys.exit(1)

@cli.command()
@click.option('--file', '-f', help='配置文件路径')
@click.pass_context
def init_config(ctx, file):
    """初始化配置文件"""
    config_file = file or "codegen_config.yaml"

    if os.path.exists(config_file):
        if not click.confirm(f"Configuration file {config_file} already exists. Overwrite?"):
            return

    config = ConfigManager()
    config.save_config(config_file)
    logger.info(f"Configuration file initialized: {config_file}")

@cli.command()
@click.pass_context
def show_config(ctx):
    """显示当前配置"""
    config = ctx.obj['config']

    print("Current Configuration:")
    print("="*40)
    print(f"Database:")
    print(f"  Host: {config.config.database.host}")
    print(f"  Port: {config.config.database.port}")
    print(f"  Database: {config.config.database.database}")
    print(f"  User: {config.config.database.user}")
    print(f"  Charset: {config.config.database.charset}")
    print()
    print(f"Generation:")
    print(f"  Output Directory: {config.config.generation.output_dir}")
    print(f"  Base Class: {config.config.generation.base_class}")
    print(f"  Include Validation: {config.config.generation.include_validation}")
    print(f"  Include Foreign Keys: {config.config.generation.include_foreign_keys}")
    print(f"  Custom Methods Protection: {config.config.generation.custom_methods_protection}")
    print(f"  Use Black: {config.config.generation.use_black}")
    print(f"  Use isort: {config.config.generation.use_isort}")
    print(f"  Line Length: {config.config.generation.line_length}")
    print()
    print(f"Excluded Tables: {config.config.excluded_tables}")

if __name__ == '__main__':
    cli()