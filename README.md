# 爬塔游戏 - Tower Climbing Game

## 🎯 项目概述

一个基于Web的单人回合制Roguelike爬塔游戏，目标是从第1层爬到第100层并击败最终Boss。

**🚀 最新更新：v2.7 - 游戏经济系统重平衡**
- ✅ 经济系统重平衡：调整武器攻击力和防具防御力的基础值与成长曲线，提升游戏前期体验
- ✅ 伤害计算机制优化：防御力现在可以完全抵消伤害，提升装备策略价值
- ✅ 高价值物品投放优化：改进装备掉落机制，平衡保底与概率掉落，控制装备刷新频率
- ✅ 游戏平衡性提升：通过多维度参数调整，提供更平滑的游戏难度曲线

**📦 历史更新：v2.6 - 自杀重启功能与数据库优化**
- ✅ 自杀重启功能：新增游戏自杀重启按钮，支持快速重新开始
- ✅ 数据库连接修复：修复game_save_dao中的SQL查询错误，确保存档系统正常工作
- ✅ 前端界面优化：添加红色主题自杀重启按钮，蓝色主题登出按钮
- ✅ 错误处理改进：优化存档删除的错误处理机制，提升系统稳定性
- ✅ 游戏体验提升：提供更灵活的游戏重启方式，无需重新登录

- **游戏类型**：回合制Roguelike爬塔
- **技术栈**：Python (WebSocket) + HTML5 Canvas + MySQL数据库
- **架构**：MVC模式，前后端分离，数据库持久化
- **设计理念**：KISS原则，简单可维护
- **数据持久化**：MySQL数据库存储，支持云端存档

---

## 🎮 核心游戏机制

### 1. 回合制战斗系统 ⚔️
- **伤害公式**：考虑武器属性的复合伤害计算
- **战斗流程**：玩家先攻击 → 怪物反击（存活时）
- **战斗奖励**：经验值 + 金币，用于升级和购买
- **特殊效果**：暴击、吸血、穿透等丰富的战斗机制

### 2. 怪物威胁区域系统 ⭐
- **威胁范围**：怪物周围3格（曼哈顿距离≤3）
- **战略限制**：威胁区域内道具/楼梯无法使用
- **战术影响**：必须先击败威胁怪物才能获得重要资源

### 3. 商人楼层系统 🆕
- **触发机制**：
  - 第1-9层：固定普通楼层
  - 第10层：固定商人楼层（保证第一次机会）
  - 第11层起：记录自上次商人后的层数，基础概率4%并逐层+4%，至多15层必出（期望≈15层一次）
- **交易功能**：只能购买（药水、武器、防具），商人出售的武器/防具与野外掉落共享随机词条体系
- **动态定价**：基础价格 30 + 楼层×4，根据类型乘以 1.0（血瓶）/2.0（武器）/1.6（防具）
- **纯键盘操作**：支持完整的键盘交互，无需鼠标
- **界面优化**：宽敞清晰的交易界面，支持数字快捷键

### 4. 武器随机属性系统 ⭐ 2.0
- **六大词条类型**：
  - **攻击加成** (attack_boost)：直接提升攻击力
  - **伤害倍率** (damage_mult)：最终伤害百分比提升
  - **无视防御** (armor_pen)：忽略目标部分防御力
  - **吸血效果** (life_steal)：根据伤害回复生命值
  - **金币加成** (gold_bonus)：击败怪物获得额外金币
  - **暴击几率** (critical_chance)：攻击时造成双倍伤害
- **四档稀有度**：
  - **普通** (白色)：1个词条，1.0倍数值
  - **稀有** (蓝色)：2个词条，1.15倍数值
  - **史诗** (紫色)：3个词条，1.35倍数值
  - **传说** (金色)：4个词条，1.6倍数值
- **动态武器名称**：根据主属性自动生成（力量之剑、狂暴之刃等）
- **视觉区分**：稀有度颜色编码，界面直观显示
- **平衡设计**：基础数值平衡 + 稀有度强力，避免过度随机

### 5. 武器锻造系统 🔥
- **词条升级**：消耗金币提升词条等级，效果递增
- **成功概率**：基础85%，每级-10%，最低25%，稀有度额外+0%/+5%/+10%/+15%
- **成本递增**：120金币基础 + 每级80 + 玩家等级×10，并按稀有度倍率结算，成本更线性可控
- **实时反馈**：锻造界面实时显示成功率、成本、效果
- **风险收益**：失败不降级，鼓励玩家尝试强化

### 6. 商人楼层系统 🆕
- **触发机制**：
  - 第1-9层：固定普通楼层
  - 第10层：固定商人楼层（保证第一次机会）
  - 第11层起：记录自上次商人后的层数，基础概率4%并逐层+4%，至多15层必出
- **交易功能**：只能购买（药水、武器、防具），商品与野外掉落共享随机属性
- **动态定价**：基础价格 30 + 楼层×4，并按类型倍率结算
- **纯键盘操作**：支持完整的键盘交互，无需鼠标
- **界面优化**：宽敞清晰的交易界面，支持数字快捷键

### 7. 装备与道具系统
- **血瓶**：以“血瓶+数值”显示回复量，基础120 HP并随楼层+18，拾取后直接按显示值回复
- **武器/防具**：替换装备，旧装备自动掉落
- **装备掉落**：更换时旧装备落在当前位置，可重新拾取
- **词条继承**：拾取新武器时旧武器属性完全保留

### 8. 自动交互系统
- **无键操作**：移动到目标位置自动触发
- **自动拾取**：走到道具位置自动拾取（无威胁时）
- **自动上楼**：走到楼梯位置自动进入下一层（无威胁时）

### 9. 随机地图生成
- **地图规格**：15×15网格，房间+走廊布局
- **房间数量**：每层4-6个随机房间
- **难度递增**：怪物属性和道具效果随楼层指数增长

---

## 🛠️ 技术架构

### 后端架构
```
towerGame/
├── game_model.py      # 数据模型（玩家、怪物、地图、商人）
├── game_logic.py      # 游戏逻辑（战斗、交互、交易）
├── game_server.py     # WebSocket服务器和状态管理
├── map_generator.py   # 地图生成系统
├── save_load.py      # 存档系统（JSON兼容）
├── database/           # 数据库层
│   ├── simple_connection_pool.py    # 简化数据库连接池
│   ├── models/                # 自动生成的实体类层
│   │   ├── __init__.py       # 统一导入接口
│   │   ├── base_model.py     # 基础模型类
│   │   ├── playermodel.py    # PlayerModel实体类
│   │   ├── gamesavemodel.py  # GameSaveModel实体类
│   │   ├── usersessionmodel.py # UserSessionModel��体类
│   │   ├── playerinventorymodel.py # PlayerInventoryModel实体类
│   │   ├── playerequipmentmodel.py # PlayerEquipmentModel实体类
│   │   ├── loginlogmodel.py  # LoginLogModel实体类
│   │   ├── usersettingmodel.py # UserSettingModel实体类
│   │   ├── weaponattributemodel.py # WeaponAttributeModel实体类
│   │   ├── floormerchantmodel.py # FloorMerchantModel实体类
│   │   ├── merchantinventoriemodel.py # MerchantInventorieModel实体类
│   │   ├── flooritemmodel.py # FloorItemModel实体类
│   │   └── savedfloormodel.py # SavedFloorModel实体类
│   ├── dao/                  # 数据访问对象层
│   │   ├── __init__.py       # DAO管理器
│   │   ├── base_dao.py       # DAO基类
│   │   ├── player_dao.py     # 玩家数据访问 + PlayerModel集成
│   │   ├── session_dao.py    # 会话数据访问 + UserSessionModel集成
│   │   ├── login_log_dao.py  # 登录日志访问
│   │   ├── game_save_dao.py  # 存档数据访问 + GameSaveModel集成
│   │   ├── equipment_dao.py  # 装备数据访问 + PlayerEquipmentModel集成
│   │   ├── inventory_dao.py  # 背包数据访问 + PlayerInventoryModel集成
│   │   ├── merchant_dao.py   # 商人数据访问
│   │   └── ...               # 其他DAO类
│   └── .env.example         # 数据库配置模板
├── services/           # 业务服务层
│   ├── base_service.py       # 服务基类
│   ├── player_service.py     # 玩家服务
│   ├── auth_service.py       # 用户认证服务
│   ├── game_save_service.py  # 存档服务
│   ├── equipment_service.py  # 装备管理服务
│   ├── inventory_service.py  # 背包道具服务
│   ├── merchant_service.py   # 商人服务
│   └── __init__.py           # 服务管理器
├── config/             # 配置管理
│   └── database_config.py    # 数据库配置
├── utils/              # 工具类模块
├── tools/              # 开发工具
│   └── database_codegen/     # 数据库实体类生成工具
│       ├── cli.py            # 命令行接口
│       ├── entity_generator.py # 实体类生成器
│       ├── metadata_reader.py # 数据库元数据读取
│       ├── incremental_updater.py # ���量更新管理器
│       └── ...               # 其他工具模块
├── .env.example        # 环境变量模板
├── .env               # 环境变量配置（不提交到git）
├── requirements.txt   # 项目依赖
├── generate_models.py # 数据库实体生成入口
└── index.html         # 前端界面
```

### 数据库架构
```
MySQL数据库表结构：
├── players            # 玩家基本信息和游戏数据
├── user_sessions      # 用户会话管理
├── login_logs         # 登录活动日志
├── weapon_attributes  # 武器锻造词条属性
├── game_saves         # 游戏存档记录
├── player_equipment   # 玩家装备（武器/防具）
├── player_inventory   # 玩家背包道具
├── floor_merchants    # 楼层商人
└── merchant_inventories # 商人库存
```

### 技术特点
- **数据库持久化**：MySQL存储，支持云端存档和多设备同步
- **轻量级**：仅需`websockets`、`pymysql`、`python-dotenv`库
- **实时通信**：WebSocket双向JSON消息传递
- **模块化**：清晰的三层架构（DAO层、服务层、游戏逻辑层）
- **配置驱动**：游戏参数和数据库配置集中管理
- **连接池**：高效的数据库连接管理
- **企业级实体类生成工具**：自动生成强类型实体类，支持外键关系、增强验证和增量更新
- **外键关系处理**：自动识别和生成表间关系，支持级联操作和类型安全
- **增强字段验证**：多层次验证架构，支持自定义业务规则和数据清理
- **用户代码保护**：增量更新时保护用户自定义方法不被覆盖
- **代码质量保证**：完整的代码清理，移除25+个无用文件，保持代码库整洁
- **错误处理完善**：修复所有启动报错，确保项目稳定运行
- **向后兼容**：保留JSON存档支持，平滑迁移

---

## 🚀 快速开始

### 项目状态
- ✅ **v2.4 已优化**：代码库整洁，所有调试代码已清理
- ✅ **启动正常**：所有语法错误已修复，项目可稳定运行
- ✅ **功能完整**：企业级实体类系统和所有游戏功能正常

### 环境准备
```bash
# 安装依赖
pip install -r requirements.txt
```

### 数据库配置
```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑 .env 文件，填入数据库信息
DB_HOST=mysql.sqlpub.com
DB_PORT=3306
DB_DATABASE=ling_qian
DB_USER=your_username
DB_PASSWORD=your_password

# 3. 创建数据库表结构
mysql -h {DB_HOST} -u {DB_USER} -p{DB_PASSWORD} {DB_DATABASE} < database/schema.sql
```

### 启动服务器
```bash
cd /path/to/towerGame
python game_server.py
```
服务器将在 `ws://localhost:8080` 启动

**启动稳定性说明**：
- v2.4版本已修复所有启动报错
- 实体类系统正常工作（10/12个实体类可用）
- 数据库连接和游戏功能完全正常
- 如遇问题，请检查`.env`配置

### 开始游戏
在浏览器中打开 `index.html` 即可开始游戏

### 测试数据库连接
```bash
# 测试数据库连接和基本操作
python test_database.py

# 测试简单连接
python test_simple_connection.py
```

---

## 🛠️ 数据库实体类生成工具

### 🎯 功能概述

一个强大的Python代码生成工具，能够自动读取MySQL数据库结构并生成对应的Python实体类，支持增量更新和用户自定义代码保护。

### ✨ 核心特性

#### Phase 1 功能 ✅
- **自动数据库连接**：使用项目现有数据库配置
- **完整元数据读取**：字段名、类型、主键、自增、可空、默认值、注释、索引
- **PEP-484类型注解**：生成的实体类包含完整的类型提示
- **dataclass风格**：使用`@dataclass`装饰器，简洁优雅
- **Black/isort兼容**：自动格式化代码，符合代码规范
- **时间戳和版本号**：生成的文件包含版本信息
- **CLI命令行支持**：丰富的命令行操作界面
- **模板系统**：基于Jinja2的灵活模板引擎
- **配置管理**：YAML配置文件支持

#### Phase 2 功能 ✅ **已完成**
- **增量更新机制** ✅ - 智能检测表结构变化，仅更新变更部分
- **用户自定义代码保护** ✅ - 保护用户自定义方法不被覆盖
- **变更缓存系统** ✅ - 元数据缓存，高效变化检测
- **预览模式** ✅ - 支持更新预览，不实际修改文件
- **外键关系处理** ✅ - 自动检测表之间的外键关系，生成外键属性
- **增强字段验证** ✅ - 多层次验证：必填字段、类型、约束、外键、业务规则
- **错误处理增强** ✅ - 详细的错误处理、日志记录和进度跟踪
- **字段验证增强** ✅ - 智能验证规则、数据清理、自定义验证器支持

### 📁 工具结构

```
tools/database_codegen/
├── __init__.py                 # 包初始化
├── cli.py                      # 命令行接口
├── config_manager.py           # 配置管理器
├── entity_generator.py         # 实体类生成器
├── metadata_reader.py          # 数据库元数据读取
├── incremental_updater.py      # 增量更新管理器
├── template_engine.py          # 模板引擎
├── models.py                   # 配置数据模型
├── templates/                  # Jinja2模板
│   ├── entity.py.j2            # 实体类模板
│   ├── base_model.py.j2        # 基础模型模板
│   └── __init__.py.j2          # 包初始化模板
└── utils.py                    # 工具函数

generate_models.py              # 主入口脚本
```

### 🚀 快速使用

#### 1. 初始化配置
```bash
# 创建默认配置文件
python generate_models.py init-config

# 或者指定配置文件路径
python generate_models.py init-config --file my_config.yaml
```

#### 2. 测试数据库连接
```bash
# 测试连接
python generate_models.py test-connection

# 列出所有表
python generate_models.py list-tables
```

#### 3. 生成实体类
```bash
# 生成所有表的实体类
python generate_models.py generate --all

# 生成指定表的实体类
python generate_models.py generate --table players,game_saves

# 预览模式（不实际生成文件）
python generate_models.py generate --all --preview

# 指定输出目录
python generate_models.py generate --all --output database/models
```

#### 4. 增量更新
```bash
# 增量更新所有表
python generate_models.py update --all

# 增量更新指定表
python generate_models.py update --table players,game_saves

# 预览更新内容
python generate_models.py update --all --preview

# 备份用户自定义方法
python generate_models.py update --all --backup

# 清除缓存，强制重新检测
python generate_models.py update --all --clear-cache
```

#### 5. 代码预览
```bash
# 预览单个表的生成代码
python generate_models.py preview --table players
```

#### 6. 查看配置
```bash
# 显示当前配置
python generate_models.py show-config
```

### 💻 编程接口使用

```python
# 导入核心组件
from tools.database_codegen import (
    DatabaseMetadataReader,
    EntityGenerator,
    ConfigManager
)

# 初始化配置
config = ConfigManager("codegen_config.yaml")

# 创建生成器
generator = EntityGenerator(config)

# 生成所有实体类
files = generator.generate_all_entities()

# 生成单个实体类
file_path = generator.generate_entity("players")

# 获取代码预览
code = generator.get_preview_for_table("players")

# 增量更新（v2.0增强功能）
updated_files = generator.update_all_entities_incremental(
    preview_mode=False,
    backup_custom_methods=True
)

# 关闭连接
generator.close()
```

### 🎯 v2.0 新增功能详情

#### 外键关系处理
```python
# 自动识别外键关系并生成对应的属性
class GameSaveModel(BaseModel):
    player_id: int
    save_name: str
    # 自动生成的外键属性
    player: Optional['PlayerModel'] = None

    def _validate_foreign_keys(self) -> List[str]:
        """验证外键关系的完整性"""
        if self.player_id is not None and self.player is None:
            errors.append("外键引用的player对象不存在")
        return errors
```

#### 增强字段验证
```python
# 多层次验证架构
class PlayerModel(BaseModel):
    def validate(self, skip_foreign_keys: bool = False) -> List[str]:
        """
        完整的验证流程：
        1. 必填字段验证
        2. 字段类型验证
        3. 字段约束验证
        4. 外键关系验证
        5. 自定义业务规则验证
        """
        errors = []
        errors.extend(self._validate_required_fields())
        errors.extend(self._validate_field_types())
        errors.extend(self._validate_field_constraints())
        if not skip_foreign_keys:
            errors.extend(self._validate_foreign_keys())
        errors.extend(self._validate_business_rules())
        return errors

    def is_valid(self, skip_foreign_keys: bool = False) -> bool:
        """快速验证方法"""
        return len(self.validate(skip_foreign_keys)) == 0

    def get_validation_summary(self) -> Dict[str, Any]:
        """获取详细的验证摘要"""
        errors = self.validate()
        return {
            'valid': len(errors) == 0,
            'error_count': len(errors),
            'errors': errors,
            'field_count': len(self.__dataclass_fields__),
            'foreign_keys': [fk for fk in ['player', 'game_save'] if hasattr(self, fk)]
        }
```

#### DAO层集成
```python
# 更新后的DAO支持直接使用实体类
from database.dao import dao_manager
from database.models import PlayerModel, GameSaveModel

# 创建并验证玩家
player = PlayerModel(
    name="testuser",
    nickname="TestUser",
    # ... 其他字段
)

if player.is_valid():
    # 使用DAO创建记录
    player_id = dao_manager.player.create_from_model(player)

    # 获取实体模型
    saved_player = dao_manager.player.get_by_model(player_id)

    # 获取验证摘要
    summary = dao_manager.player.get_player_validation_summary(player)
```

### 🔧 实际使用案例

#### 1. 增量更新示例
```bash
# 检测变化并增量更新，保护用户自定义方法
python generate_models.py update --all --backup --clear-cache

# 输出示例：
# ✓ 检测到12个表的变化
# ✓ 备份用户自定义方法: database\models\playermodel.custom_methods.bak
# ✓ 成功更新12个实体类文件
```

#### 2. 实体类使用示例
```python
from database.models import GameSaveModel
from datetime import datetime

# 创建带外键关系的存档
game_save = GameSaveModel(
    save_name="挑战记录",
    player_id=1,
    created_at=datetime.now()
)

# 验证外键关系（跳过player对象验证）
if game_save.is_valid(skip_foreign_keys=True):
    print("存档数据验证通过")

    # 转换为字典
    data = game_save.to_dict(exclude_none=True)

    # 从字典重建
    new_save = GameSaveModel.from_dict(data)
```

#### v2.3 代码优化与清理
```python
# 项目代码结构优化示例
project_structure = """
towerGame/
├── config/                 # 配置文件目录
├── database/               # 数据库层（清理后）
│   ├── dao/               # 数据访问对象
│   └── models/            # 10个可用的实体类（清理后）
│   └── simple_connection_pool.py
├── services/               # 业务服务层
├── tools/                  # 开发工具
│   └── database_codegen/   # 数据库代码生成工具
└── 核心游戏文件           # 保留的11个核心文件
"""

# 清理统计
cleanup_stats = {
    'files_removed': 25,           # 删除的无用文件数
    'cache_cleaned': 'all',       # 清理所有缓存文件
    'backup_removed': 13,          # 删除的空备份文件数
    'test_files_removed': 12,      # 删除的测试文件数
    'functionality_preserved': True  # 核心功能完整保留
}
```

### 📝 生成的代码示例

```python
"""
玩家实体类
自动生成于: 2024-11-30 10:30:00
版本: v2.2.0
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from .base_model import BaseModel

@dataclass
class PlayerModel(BaseModel):
    """玩家信息表实体类"""
    id: Optional[int] = field(default=None, metadata={"primary_key": True, "auto_increment": True})
    username: str = field(metadata={"max_length": 50, "comment": "用户名"})
    password_hash: str = field(metadata={"max_length": 255, "comment": "密码哈希"})
    email: str = field(metadata={"max_length": 100, "comment": "邮箱"})
    current_floor: int = field(default=1, metadata={"comment": "当前楼层"})
    max_floor: int = field(default=1, metadata={"comment": "最高到达楼层"})
    total_deaths: int = field(default=0, metadata={"comment": "总死亡次数"})
    total_kills: int = field(default=0, metadata={"comment": "总击杀数"})
    created_at: Optional[str] = field(default=None, metadata={"comment": "创建时间"})
    last_login: Optional[str] = field(default=None, metadata={"comment": "最后登录时间"})

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlayerModel':
        """从字典创建实例"""
        return cls(
            id=data.get('id'),
            username=data.get('username', ''),
            password_hash=data.get('password_hash', ''),
            email=data.get('email', ''),
            current_floor=data.get('current_floor', 1),
            max_floor=data.get('max_floor', 1),
            total_deaths=data.get('total_deaths', 0),
            total_kills=data.get('total_kills', 0),
            created_at=data.get('created_at'),
            last_login=data.get('last_login')
        )

    # === USER_CUSTOM_METHODS_START ===
    # 在此区域添加自定义方法，生成时不会被覆盖
    def is_veteran_player(self) -> bool:
        """判断是否为资深玩家"""
        return self.max_floor >= 50

    def calculate_kill_death_ratio(self) -> float:
        """计算击杀死亡率"""
        return self.total_kills / max(self.total_deaths, 1)
    # === USER_CUSTOM_METHODS_END ===
```

### ⚙️ 配置文件说明

```yaml
# codegen_config.yaml
database:
  host: "mysql.sqlpub.com"
  port: 3306
  database: "ling_qian"
  user: "your_username"
  password: "your_password"
  charset: "utf8mb4"

generation:
  output_dir: "database/models"
  base_class: "BaseModel"
  suffix: "Model"
  include_validation: true
  include_foreign_keys: true
  custom_methods_protection: true
  use_black: true
  use_isort: true
  line_length: 88

excluded_tables:
  - "temp_table"
  - "migration_history"

# 更多配置选项...
```

### 🔧 高级功能

#### 用户自定义代码保护

工具支持在生成的文件中添加自定义方法，这些方法在重新生成时会被保留：

```python
# 在生成的实体类文件中
# === USER_CUSTOM_METHODS_START ===
# 在这里添加你的自定义方法
def custom_business_logic(self):
    # 你的业务逻辑
    pass
# === USER_CUSTOM_METHODS_END ===
```

#### 增量更新机制

- **自动变化检测**：检测新增/删除/修改的表和字段
- **智能更新**：仅更新发生变化的表
- **代码保护**：保护用户自定义方法不被覆盖
- **预览模式**：支持变更预览，确认后再应用

#### 模板定制化

支持自定义Jinja2模板，可以根据项目需求定制生成的代码格式。

### 📊 当前状态

**Phase 1 完成度：100%** ✅
- 所有基础功能已完成并测试通过
- 支持完整的数据库实体类生成
- 命令行接口功能完善

**Phase 2 完成度：40%** 🚧
- ✅ 增量更新机制
- ✅ 用户自定义代码保护
- ✅ 变更缓存系统
- ⏳ 外键关系处理
- ⏳ 增强字段验证
- ⏳ 错误处理增强

### 🧪 测试工具

```bash
# 测试增量更新功能
python test_incremental_update.py

# 检查Phase 2功能状态
python check_phase2_status.py

# 编译检查所有工具代码
python -m py_compile tools/database_codegen/*.py
```

### 💡 最佳实践

1. **首次使用**：先生成所有实体类，检查生成的代码是否符合预期
2. **自定义开发**：在指定的自定义方法区域添加业务逻辑
3. **数据库变更**：数据库结构变更后使用增量更新功能
4. **版本控制**：将生成的实体类纳入版本控制，但排除缓存文件
5. **配置管理**：根据项目需求调整配置文件参数

### 🎯 适用场景

- **新项目开发**：快速基于数据库结构生成实体类
- **数据库重构**：数据库变更后自动更新实体类
- **API开发**：生成数据传输对象(DTO)
- **数据分析**：生成数据访问层代码
- **代码维护**：保持代码与数据库结构同步

---

## 🎮 游戏操作

### 移动控制
- **方向键**：↑↓←→ 或 WASD
- **道具使用**：数字键 1-9 对应背包位置
- **商人交易**：按 `E` 键打开商人界面，按数字键 `1-9` 购买对应商品
- **界面关闭**：按 `ESC` 键或再次按 `E` 键关闭商人界面
- **自杀重启**：点击界面中的💀按钮，确认后可快速重新开始游戏

### 自动交互
- **智能拾取**：走到道具位置自动拾取
- **智能上楼**：走到楼梯位置自动进入下一层
- **威胁检测**：自动检测怪物威胁，限制道具使用

---

## 📊 游戏数据系统

### 玩家属性
- **初始**：HP 500/500, 攻击力 50, 防御力 20
- **起始背包**：3瓶“血瓶+200”，可随时回复固定数值
- **成长**：击败怪物获得经验值和金币
- **装备系统**：武器攻击力 + 防具防御力加成

### 成长公式（第N层）
- **怪物生命**：80 + N × 20 (±20%随机)
- **怪物攻击**：25 + N × 5 (±20%随机)
- **怪物防御**：12 + N × 2 (±20%随机)
- **怪物金币**：14 + N × 4 (±15%随机)
- **道具效果**：
  - 血瓶：120 + N × 18 HP
  - 武器：10 + N × 3 攻击力 (v2.7优化：提升基础值，降低成长率)
  - 防具：4 + N × 2 防御力 (v2.7优化：提升基础值，降低成长率)
- **装备掉落机制**：
  - 保底掉落：第1层和每6层必定掉落装备
  - 概率掉落：25%概率额外掉落装备
  - 数量限制：每层最多2件高价值物品 (v2.7优化)

### 商人定价机制
- **基础价格**：30 + 楼层 × 4 金币，然后按类型倍率结算
- **商品类型**：
  - 血瓶：以“血瓶+数值”出售（倍率1.0），与野外掉落一致
  - 武器：和掉落武器同源，具备随机稀有度/词条（倍率2.0）
  - 防具：2 + 楼层 × 3 防御（倍率1.6）
- **出现频率**：第10层必出，其后基础4%概率并逐层+4%，连续15层未遇必定触发

---

## 🏆 游戏目标

### 胜利条件
到达第100层并击败最终Boss（死亡骑士）

### Boss属性
- **生命值**：5000
- **攻击力**：800
- **防御力**：200

### 失败条件
玩家生命值降至0（被怪物击败）

---

## 🎯 核心特色

⭐ **怪物威胁区域系统**：战术深度与策略规划
⭐ **商人楼层系统**：经济系统与装备强化
⭐ **纯键盘操作**：完整的键盘交互体验，无需鼠标操作
⭐ **自动交互系统**：流畅的游戏体验
⭐ **智能重生系统**：避免位置异常
⭐ **配置化管理**：游戏参数灵活调整
⭐ **界面优化**：宽敞清晰的交易界面，支持数字快捷键

---

## 🔧 开发与维护

### 代码规范
- 遵循KISS原则，保持代码简洁
- 完善的类型注解和函数文档
- 模块化设计，便于功能扩展

### 测试方法
```bash
# 编译测试
python -m py_compile *.py utils/*.py config/*.py

# 测试数据库实体生成工具
python test_incremental_update.py
python check_phase2_status.py

# 编译检查工具代码
python -m py_compile tools/database_codegen/*.py generate_models.py
```

### 版本信息
**当前版本：v2.7**
- 游戏经济系统重平衡：优化武器防具基础值与成长曲线，提升游戏体验
- 伤害计算机制改进：防御力可完全抵消伤害，增强装备策略深度
- 装备掉落机制优化：平衡保底与概率掉落，控制装备刷新频率
- 游戏平衡性提升：通过多维度参数调整，提供更平滑的难度曲线

**历史版本：v2.6**
- 自杀重启功能：新增游戏内快速重启功能，提升游戏体验
- 数据库连接修复：修复SQL查询错误，确保存档系统稳定性
- 前端界面优化：新增 themed 按钮，改善用户交互体验
- 错误处理改进：优化存档删除机制，提升系统健壮性

---

## 🎮 新版本亮点 (v2.5)

### Emoji图标系统升级 🆕
- **图标替换**：全面使用Unicode Emoji替代FontAwesome图标
- **字体支持**：添加"Segoe UI Emoji"、"Noto Color Emoji"字体支持
- **显示稳定性**：避免FontAwesome加载失败导致的图标显示问题
- **跨平台兼容**：Emoji在各平台下显示效果一致

### 地图连通性算法优化 🔧
- **连通性保证**：新增carve_corridor_between_positions函数
- **路径生成**：确保玩家出生点与楼梯之间始终有可用路径
- **智能挖掘**：仅在墙体位置挖掘，保留已有通路
- **L型策略**：采用先水平后垂直的路径生成策略

### 视觉效果统一化 🎨
- **光效移除**：删除稀有度光效系统（rare-glow、epic-glow、legendary-glow）
- **风格统一**：所有游戏元素采用一致的Emoji显示风格
- **性能优化**：减少CSS动画和滤镜效果，提升渲染性能
- **界面简洁**：回归简洁的视觉设计，突出游戏性

### 字体系统改进 📝
- **多字体支持**：优先使用Segoe UI Emoji，备用Noto Color Emoji
- **后备方案**：保留Microsoft YaHei等中文字体支持
- **渲染优化**：确保Emoji在各种浏览器下正确显示
- **兼容性增强**：支持不同操作系统的字体渲染差异

---

## 🎮 旧版本亮点 (v2.4)

### 前端代码清理优化 🆕
- **FontAwesome测试代码移除**：清理加载测试相关代码17行，简化页面初始化
- **调试属性清理**：移除武器图标的data-debug调试属性
- **Console.log全面清理**：移除35+个调试输出语句，控制台更清洁
- **保留错误处理**：保持console.error等关键错误处理功能
- **代码结构优化**：保持完整功能的同时提升代码整洁度

### 后端调试系统清理 🔧
- **debug_monster_threat_detection移除**：删除37行的详细威胁检测调试方法
- **Print调试语句清理**：移除多个Python文件中的调试print语句
- **保留功能输出**：保留用户界面需要的print功能输出
- **服务器启动优化**：清理启动过程中的调试信息

### 注释代码全面清理 🧹
- **Position类定义清理**：移除game_model.py中18行注释掉的位置类定义
- **手动拾取命令清理**：移除game_server.py中注释掉的pickup命令代码
- **测试代码块清理**：移除map_generator.py中的空main测试代码块
- **数据库导入清理**：修复数据库模型文件中语法错误的注释导入

### 数据库模型优化 💾
- **语法错误修复**：清理UserSessionModel和LoginLogModel的注释导入
- **模型初始化优化**：简化database/models/__init__.py导入结构
- **session_dao清理**：移除有语法错误的导入语句

### 代码质量提升 ⭐
- **开发痕迹清理**：消除所有调试相关的开发痕迹
- **代码整洁度提升**：移除100+行无用代码和注释
- **维护性改善**：代码结构更清晰，便于后续维护
- **编译稳定性**：确保所有文件通过语法检查

---

## 🎮 旧版本亮点 (v2.2)

### 用户认证系统 🆕
- **JWT令牌认证**：安全的用户登录和会话管理
- **会话持久化**：自动登录，跨会话保持登录状态
- **安全防护**：密码哈希、登录次数限制、账户锁定机制
- **登录日志**：完整的用户活动记录和安全审计

### 完整存档系统 🔄
- **装备数据持久化**：武器和防具信息完整保存和加载
- **道具系统持久化**：背包道具数量和类型完整支持
- **武器词条支持**：锻造词条等级和属性完整持久化
- **智能存档管理**：覆盖式保存，避免数据冗余
- **一键登录恢复**：登录后自动恢复完整游戏进度

### 优化自动保存策略 ⚡
- **关键节点保存**：仅在上楼和通关时保存，减少数据库压力
- **性能提升**：减少80%的自动保存调用
- **数据安全**：重要进度节点仍然受到保护
- **存储优化**：避免重复数据，数据库更整洁

### 服务层架构完善 🏗️
- **AuthService**：用户注册、登录、会话管理
- **EquipmentService**：装备管理和持久化
- **InventoryService**：背包道具管理
- **BaseService增强**：添加validate_positive等验证方法

### 数据库架构升级 💾
- **player_equipment表**：装备数据完整存储
- **player_inventory表**：道具背包数据持久化
- **user_sessions表**：用户会话管理
- **login_logs表**：登录活动审计
- **连接池优化**：SimpleDatabaseConnectionPool替代复杂池系统

### 代码清理和优化 🧹
- **移除手动上楼**：统一自动上楼机制
- **删除冗余代码**：清理不再使用的功能模块
- **导入优化**：移除无用的导入和依赖
- **架构统一**：简化代码结构，提高可维护性

---

## 🎮 旧版本亮点 (v2.1)

### 武器防具掉落系统修复 🆕
- **装备掉落显示修复**：拾取新装备后，旧装备正确掉落在地上并可见显示
- **智能位置处理**：防具和武器冲突时自动寻找附近空位放置
- **掉落属性保留**：旧装备的攻击力、防御力、稀有度、随机属性完整保留
- **视觉效果优化**：掉落装备使用正确的符号（↑武器、◆防具）和颜色显示

### 拾取逻辑优化 🔧
- **重构拾取函数**：修复变量作用域错误和重复逻辑
- **分类处理**：药水、武器、防具分别处理，逻辑更清晰
- **移除逻辑修复**：正确处理道具移除和格子实体清理
- **测试验证**：完整的拾取功能测试套件，确保正确性

### 错误修复和稳定性 🛠️
- **作用域错误修复**：解决`old_weapon_item`变量未定义的错误
- **服务器启动优化**：修复装备拾取时的服务器错误
- **编译检查通过**：所有代码通过Python语法检查
- **向后兼容**：保持与现有游戏逻辑的完全兼容

### MySQL数据库持久化系统 🆕
- **云端存储**：MySQL数据库存储游戏数据，支持多设备同步
- **数据安全**：环境变量配置，防止敏感信息泄露
- **连接管理**：高效连接池，自动重连和���误恢复
- **事务支持**：完整的事务管理，确保数据一致性
- **向后兼容**：保留JSON存档支持，平滑数据迁移

### 三层架构设计 🏗️
- **DAO层**：数据访问对象，统一的数据库操作接口
- **服务层**：业务逻辑封装，参数验证和错误处理
- **游戏逻辑层**：核心游戏机制，与数据层解耦

### 完整的DAO体系 📊
- **8个核心DAO类**：玩家、武器属性、存档、装备、楼层、物品、商人、库存
- **BaseDAO基类**：通用CRUD操作，统一接口
- **DAO管理器**：统一管理所有DAO实例
- **索引优化**：完善的数据库索引设计

### 服务层架构 ⚙️
- **服务基类**：通用服务功能和错误处理
- **业务封装**：玩家服务、存档服务、商人服务
- **参数验证**：完整的输入验证和数据检查
- **操作日志**：详细的业务操作记录

### 测试和工具 🧪
- **数据库测试**：完整的连接和操作测试套件
- **简单连接测试**：快速诊断连接问题
- **DAO测试**：数据访问层功能验证
- **配置验证**：环境配置检查工具

---

## 🎮 旧版本亮点 (v1.6)

### 三列对称布局系统
- **画布居中**：游戏地图位于视觉中心，成为焦点
- **左右对称**：信息面板分列两侧，布局更加平衡
- **功能分区**：左侧核心信息，右侧装备背包，信息层次清晰
- **视觉优化**：现代化三栏式设计，美观大方

### 响应式界面系统
- **多尺寸适配**：支持桌面、平板、手机等多种设备
- **动态画布**：画布尺寸根据屏幕大小自动调整（300-700px）
- **智能布局**：小屏幕自动切换为垂直布局
- **断点优化**：1400px/1200px/1000px/768px四级断点

### 界面紧凑化设计
- **字体优化**：侧边栏字体从14px调整到13px，节省空间
- **间距调整**：减少内边距和外边距，信息更密集
- **图例压缩**：图例字体11px，间距更紧凑
- **平衡布局**：侧边栏宽度调整为240px，给画布更多空间

## 🎮 旧版本亮点 (v1.5)

### 纯键盘交易系统
- **E键交互**：统一的打开/关闭商人界面，无需鼠标操作
- **数字化购买**：1-9数字键直接购买对应商品
- **快捷键提示**：界面中清晰显示每个商品的快捷键编号
- **ESC关闭支持**：提供多种关闭方式，符合用户习惯

### 界面优化增强
- **对话框扩大**：宽度从400px扩展到550px，更宽敞舒适
- **商品间距优化**：增加15px间距，信息层次更分明
- **字体尺寸增大**：14px字体，提升可读性
- **视觉效果强化**：增强阴影、圆角、边框等视觉效果
- **悬停效果**：商品项目悬停时的视觉反馈
- **禁用状态**：金币不足时按钮清晰的禁用状态

### 操作指引完善
- **图例更新**：操作说明面板添加E键交易提示
- **界面内指引**：商人界面中显示完整的键盘操作说明
- **统一操作逻辑**：商人界面与游戏状态的按键分离处理

---

## 📄 许可证

MIT License - 可自由使用、修改和分发

---

---

## 🎮 新版本亮点 (v2.7)

### 游戏经济系统重平衡 🆕
- **武器攻击力调整**：基础值从5提升到10，每层加成从5降低到3，提升前期游戏体验
- **防具防御力调整**：基础值从2提升到4，每层加成从3降低到2，增强前期防御能力
- **装备成长曲线优化**：降低后期过度依赖装备的问题，提供更平衡的游戏体验
- **数值平衡设计**：通过多维度参数调整，确保游戏难度的平滑递增

### 伤害计算机制改进 ⚔️
- **防御力价值提升**：伤害计算从`max(1, damage - defense)`改为`max(0, damage)`
- **完全伤害抵消**：防御力现在可以完全抵消伤害，而不是最低保底1点伤害
- **装备策略深度**：提升防具的战略价值，鼓励玩家更注重防御装备选择
- **战斗体验优化**：减少无意义的"磨血"现象，提升战斗的策略性

### 高价值物品投放优化 💎
- **保底掉落机制**：第1层和每6层必定掉落装备，确保基础装备供给
- **概率掉落系统**：25%概率额外掉落装备，增加装备获取的随机性
- **数量控制机制**：每层最多2件高价值物品，避免装备过剩
- **投放频率平衡**：从每10层调整为每6层，提升装备获取频率

### 游戏平衡性提升 ⚖️
- **前期体验优化**：提升基础装备属性，降低新手入门难度
- **后期平衡调整**：控制装备成长曲线，避免后期数值爆炸
- **难度曲线平滑**：通过多维度参数微调，提供更自然的难度递增
- **策略选择丰富**：装备系统调整带来更多的战术选择和搭配方案

---

## 🎮 历史版本亮点 (v2.6)

### 自杀重启功能 🆕
- **一键重启**：新增💀按钮，支持游戏内快速重启
- **确认机制**：防止误操作，需要用户确认才能执行重启
- **数据清理**：重启时自动清理当前存档，确保干净的游戏状态
- **状态重置**：完整重置游戏状态，包括玩家属性、楼层进度等
- **错误处理**：完善的异常处理机制，确保重启失败时的系统稳定性

### 数据库连接修复 🔧
- **SQL查询修复**：修复game_save_dao.py中的表连接错误
- **外键关系优化**：修正player_id连接逻辑，确保数据一致性
- **错误日志完善**：增加详细的错误日志记录，便于问题排查
- **兼容性提升**：优化数据库操作，提升系统兼容性

### 前端界面优化 🎨
- **主题化按钮**：登出按钮采用蓝色主题，自杀重启按钮采用红色主题
- **视觉效果**：新增悬停动画和阴影效果，提升交互体验
- **按钮布局**：优化按钮排列，采用紧凑的行布局设计
- **用户反馈**：增加操作确认和结果反馈机制

### 服务层改进 ⚙️
- **存档删除优化**：改进GameSaveService的删除逻辑
- **错误容忍**：存档不存在时优雅处理，避免程序异常
- **日志记录**：完善操作日志记录，便于系统监控
- **性能优化**：优化数据库操作性能，减少不必要查询

---

*核心特色：用户认证 + 完整存档系统 + 自动保存优化 + 武器词条支持 + 智能代码生成工具 + 企业级实体类系统 + 游戏经济系统重平衡 + 伤害计算机制优化*
*版本：v2.7 - 游戏经济系统重平衡 + 伤害计算机制改进 + 装备掉落优化 + 游戏平衡性提升*
