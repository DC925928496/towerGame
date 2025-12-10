# 爬塔游戏 - Tower Climbing Game

## 🎯 项目概述

一个基于Web的单人回合制Roguelike爬塔游戏，目标是从第1层爬到第100层并击败最终Boss。

**🚀 最新更新：v2.14 - 数据库实体类重构移除外键约束**
- ✅ **数据库实体类重构**：删除所有外键约束后重新生成实体类，优化数据结构和性能
- ✅ **实体类语法修复**：修复生成过程中出现的缩进错误，确保所有实体类语法正确
- ✅ **代码生成优化**：更新导入语句格式，统一时间戳，提升生成代码质量
- ✅ **缓存文件清理**：删除所有__pycache__目录和.pyc文件，保持代码库整洁
- ✅ **v2.13功能保留**：药瓶机制重构 + 装备掉落优化 + 跨平台部署支持 + 本地调试体验改进

**📦 历史更新：v2.13 - 药瓶机制重构 + 装备掉落优化 + 跨平台部署支持**
- ✅ **药瓶机制重构**：改为小/中/大三档药瓶，分别回复最大生命的25%/50%/75%，并与防具"药水增效"词条联动
- ✅ **装备掉落逻辑优化**：每层最多生成1把武器和1件防具，避免同层多把武器或多件防具堆叠
- ✅ **跨平台部署支持**：新增 Linux 部署文档，支持通过 Nginx 托管 index.html 并反向代理 WebSocket
- ✅ **本地调试体验改进**：前端自动根据协议与域名选择 WebSocket 地址，支持多种部署环境

**📦 关键版本里程碑：**
**v2.9 - 防具词条系统**
- ✅ 9个防具核心词条与武器系统形成混合词条体系
- ✅ 四档稀有度系统：普通(1词条) → 稀有(2词条) → 史诗(3词条) → 传说(4词条)
- ✅ 动态防具生成 + 完整战斗反馈系统 + 数据库统一存储

**v2.8 - 武器系统大升级**
- ✅ 武器词条从9个扩展到15个完整属性体系
- ✅ 新增词条类型：反击伤害、伤害减免、百分比伤害、层数加成、幸运一击、怒火模式
- ✅ 数据库智能重试机制 + 帮助弹窗系统 + 界面现代化升级

**v2.7 - 游���经济系统重平衡**
- ✅ 武器防具基础值与成长曲线优化，提升前期体验
- ✅ 伤害计算机制改进：防御力可完全抵消伤害
- ✅ 装备掉落机制优化：保底与概率平衡，控制刷新频率

**v2.6 - 核心功能优化**
- ✅ 自杀重启功能：游戏内快速重新开始
- ✅ 数据库连接修复 + 前端界面优化 + 错误处理改进

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
- **动态定价**：基础价格 30 + 楼层×4，根据类型乘以 1.0（药瓶）/2.0（武器）/1.6（防具）
- **交互方式**：商店和锻造以鼠标点击为主，E / ESC 负责开关界面
- **界面优化**：宽敞清晰的交易界面，双列表支持独立滚动

### 4. 防具随机属性系统 🛡️ v2.9
- **九大防具词条类型**：
  - **防御强化** (defense_boost)：直接提升总防御力
  - **伤害减免** (damage_reduction)：按百分比减少受到的伤害（乘法计算）
  - **荆棘反射** (thorn_reflect)：受到攻击时反弹部分伤害给攻击者
  - **格挡几率** (block_chance)：概率触发格挡，减少60%伤害
  - **闪避几率** (dodge_chance)：概率完全避免伤害
  - **生命加成** (hp_boost)：提升生命值上限
  - **上楼回血** (floor_heal)：进入新楼层时自动回复生命值
  - **击杀回血** (kill_heal)：击败敌人后回复生命值
  - **药水增效** (potion_boost)：提升药水治疗效果
- **四档稀有度系统**：
  - **普通** (白色)：1个词条，1.0倍数值
  - **稀有** (蓝色)：2个词条，1.15倍数值
  - **史诗** (紫色)：3个词条，1.35倍数值
  - **传说** (金色)：4个词条，1.6倍数值
- **权重分布设计**：
  - **防御属性(60%)**：defense_boost, damage_reduction, thorn_reflect, block_chance, dodge_chance
  - **生存属性(40%)**：hp_boost, floor_heal, kill_heal, potion_boost
- **动态名称生成**：根据主属性自动生成防具名称（钢铁胸甲、敏捷护手、生命战衣等）
- **战斗效果反馈**：详细的防具效果日志，包括伤害减免、格挡、闪避等视觉反馈
- **平衡设计理念**：专注Roguelike游戏机制，避免传统RPG中无用的死亡保护属性

### 5. 武器随机属性系统 ⭐ 3.0
- **十五大词条类型**：
  - **攻击加成** (attack_boost)：直接提升攻击力
  - **伤害倍率** (damage_mult)：最终伤害百分比提升
  - **无视防御** (armor_pen)：忽略目标部分防御力
  - **吸血效果** (life_steal)：根据���害回复生命值
  - **金币加成** (gold_bonus)：击败怪物获得额外金币
  - **暴击几率** (critical_chance)：攻击时造成双倍伤害
  - **连击几率** (combo_chance)：触发额外攻击（无反击）
  - **击杀回血** (kill_heal)：击败敌人后回复生命值
  - **经验加成** (exp_bonus)：击败怪物获得额外经验值
  - **反击伤害** (thorn_damage)：受到攻击时反弹15%伤害（v2.8新增）
  - **伤害减免** (damage_reduction)：减少5%受到的伤害（乘法计算）（v2.8新增）
  - **百分比伤害** (percent_damage)：按目标最大生命值造成3%额外伤害（v2.8新增）
  - **层数加成** (floor_bonus)：每深入一层攻击力+1（v2.8新增）
  - **幸运一击** (lucky_hit)：2%概率造成3倍伤害（v2.8新增）
  - **怒火模式** (berserk_mode)：血量低于30%时攻击力+50%（v2.8新增）
- **四档稀有度**：
  - **普通** (白色)：1个词条，1.0倍数值
  - **稀有** (蓝色)：2个词条，1.15倍数值
  - **史诗** (紫色)：3个词条，1.35倍数值
  - **传说** (金色)：4个词条，1.6倍数值
- **连击机制** (v2.7新增)：
  - 第一次连击：50%概率，造成主攻击25%伤害（无反击）
  - 第二次连击：25%概率，造成主攻击50%伤害（无反击）
  - 第三次连击：5%概率，造成主攻击75%伤害（无反击）
  - 连击吸血：所有连击都能触发吸血效果
- **击杀回血** (v2.7新增)：击败敌人后立即回复固定生命值
- **经验加成** (v2.7新增)：提升击败怪物获得的经验值，加速升级
- **反击伤害** (v2.8新增)：根据受到的伤害反弹部分伤害给怪物
- **伤害减免** (v2.8新增)：按乘法计算减免受到的所有伤害
- **百分比伤害** (v2.8新增)：对Boss最多造成5%最大生命值的额外伤害
- **层数加成** (v2.8新增)：随着深入爬塔，武器攻击力持续增长
- **幸运一击** (v2.8新增)：极低概率的爆发伤害，增加战斗的戏剧性
- **怒火模式** (v2.8新增)：绝地反击机制，低血量时大幅提升攻击力
- **动态武器名称**：根据主属性自动生成（力量之剑、连击之刃、嗜血之斧等）
- **视觉区分**：稀有度颜色编码，界面直观显示
- **平衡设计**：基础数值平衡 + 稀有度强力，避免过度随机

### 5. 武器锻造系统 🔥
- **词条升级**：消耗金币提升词条等级，效果递增
- **成功概率**：基础85%，每级-10%，最低25%，稀有度额外+0%/+5%/+10%/+15%
- **成本递增**：120金币基础 + 每级80 + 玩家等级×10，并按稀有度倍率结算，成本更线性可控
- **实时反馈**：锻造界面实时显示成功率、成本、效果
- **风险收益**：失败不降级，鼓励玩家尝试强化


### 7. 装备与道具系统
- **药瓶**：分为小/中/大三种，分别回复最大生命的25%/50%/75%，拾取后立即按百分比回复，受防具“药水增效”词条加成
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
├── save_load.py      # 旧版本地 JSON 存档清理脚本（当前版本使用数据库存档）
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
│   │   ├── weapon_attribute_dao.py  # 武器属性数据访问
│   │   └── equipment_attribute_dao.py  # 装备属性统一访问(武器防具通用) v2.9新增
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
├── weapon_attributes  # 装备属性表（武器防具通用，支持equipment_type字���）v2.9更新
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
- **存档策略**：当前版本统一使用数据库存档，旧版 JSON 存档仅支持清理（无迁移，直接替换）

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
- **起始背包**：3瓶“小药瓶”，每瓶默认回复最大生命的25%
- **成长**：击败怪物获得经验值和金币
- **装备系统**：武器攻击力 + 防具防御力加成

### 成长公式（第N层）
- **怪物生命**：80 + N × 20 (±20%随机)
- **怪物攻击**：25 + N × 5 (±20%随机)
- **怪物防御**：12 + N × 2 (±20%随机)
- **怪物金币**：14 + N × 4 (±15%随机)
- **道具效果**：
  - 药瓶：小/中/大分别回复最大生命的25%/50%/75%
  - 武器：10 + N × 3 攻击力 (v2.7优化：提升基础值，降低成长率)
  - 防具：4 + N × 2 防御力 (v2.7优化：提升基础值，降低成长率)
- **装备掉落机制**：
  - 保底掉落：第1层和每6层必定掉落装备
  - 概率掉落：25%概率额外掉落装备
  - 数量限制：每层最多2件高价值物品 (v2.7优化)

### 商人定价机制
- **基础价格**：30 + 楼层 × 4 金币，然后按类型倍率结算
- **商品类型**：
  - 药瓶：以小/中/大药瓶出售（倍率1.0，价格按回血百分比缩放），与野外掉落一致
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
⭐ **商人交互体验**：鼠标点击执行交易 / 锻造，E / ESC 快速开关
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
**当前版本：v2.14**
- **数据库实体类重构**：删除所有外键约束后重新生成实体类，优化数据结构和性能
- **实体类语法修复**：修复生成过程中出现的缩进错误，确保所有实体类语法正确
- **代码生成优化**：更新导入语句格式，统一时间戳，提升生成代码质量
- **v2.13 功能保留**：药瓶机制重构 + 装备掉落优化 + 跨平台部署支持 + 本地调试体验改进

**历史版本：v2.13**
- **药瓶机制重构**：改为小/中/大三档药瓶，分别回复最大生命的25%/50%/75%，并与防具"药水增效"词条联动（无迁移，直接替换旧"血瓶+数值"机制）
- **装备掉落逻辑优化**：每层最多生成1把武器和1件防具，避免同层多把武器或多件防具堆叠，同时保留保底+概率的整体节奏
- **跨平台部署支持**：新增 Linux 部署文档 `DEPLOY_LINUX.md`，支持通过 Nginx 托管 `index.html` 并反向代理 WebSocket `/ws` 到 Python 后端
- **本地调试体验改进**：前端自动根据协议与域名选择 WebSocket 地址，支持 Linux 部署的同时保留 Windows 本地 `file://` + `ws://localhost:8080` 调试流程
- **无用代码清理**：移除旧版药瓶兼容逻辑及相关注释，保持代码与文档一致性

**历史版本：v2.12**
- **缓存文件清理**：删除所有__pycache__目录和.pyc文件，保持代码库整洁
- **文档结构优化**：清理README.md中的重复描述，优化文档结构和可读性
- **代码质量提升**：移除无用注释和调试代码，提高代码可维护性
- **git状态优化**：清理未跟踪的临时文件，优化版本控制状态
- **词条数值展示优化**：武器/防具词条在生成、锻造与重铸时，非百分比类属性统一进行数值舍入，默认按整数展示，少数强化/重铸场景最多保留两位小数（百分比属性统一保留一位小数），修复显示不一致和长小数的问题
- **商人防具属性修复**：商人出售防具包含完整稀有度与词条信息，购买后属性完整生效并正确显示

**历史版本：v2.11**
- **双栏商人界面**：购物与锻造并列显示，列表各自滚动，信息密度更高
- **鼠标优先操作**：商品/锻造操作全部改为点击执行，E / ESC 仅负责开关界面
- **日志可视区域**：商人遮罩上移，底部日志与状态栏始终可见
- **帮助说明更新**：游戏内帮助与 README 同步新操作逻辑，去除过期的纯键盘描述

**历史版本：v2.10**
- **代码库清理与优化**：删除9个无用测试文件和临时工具，移除所有__pycache__目录，提升项目整洁度
- **启动代码优化**：简化服务器启动日志，减少冗余输出，提升启动效率
- **防具平衡调整**：优化防具词条权重分布和数值设置，提升游戏平衡性和可玩性
- **界面细节优化**：调整防具显示样式，统一界面元素命名规范，提升用户体验

**历史版本：v2.9**
- 防具词条系统完整实现：新增9个防具核心词条，与武器系统形成完整的混合词条体系
- 数据库架构升级：扩展weapon_attributes表支持equipment_type字段，实现武器防具统一存储
- 战斗反馈系统增强：新增防具效果详细日志，包括伤害减免、格挡、闪避等视觉反馈
- 前端界面优化：防具卡片式显示，支持词条列表和稀有度颜色，与武器系统UI统一
- Roguelike平衡设计：专注实用属性设计，60%防御属性+40%生存属性的合理权重分布

**历史版本：v2.8**
- 武器系统大升级：新增6个中低优先级词条，从9个扩展到15个完整武器属性体系
- 新增词条类型：反击伤害、伤害减免、百分比伤害、层数加成、幸运一击、怒火模式
- 数据库连接优化：实现智能重试机制，支持连接超时自动重连，提升系统稳定性
- 界面体验升级：新增帮助弹窗系统，优化武器展示卡片式设计，界面更加现代化
- 代码清理优化：移除无用代码和文件，优化项目结构，提升代码可维护性

**历史版本：v2.7**
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

## 📄 许可证

MIT License - 可自由使用、修改和分发

---

*核心特色：用户认证 + 完整存档系统 + 自动保存优化 + 15个武器词条支持 + 9个防具词条支持 + 混合词条体系 + 智能代码生成工具 + 企业级实体类系统 + 数据库结构优化 + 游戏经济系统重平衡 + 帮助弹窗系统 + 数据库智能重试 + 代码库清理优化 + Roguelike平衡设计*
*版本：v2.14 - 数据库实体类重构（移除外键约束后重新生成） + 实体类语法修复（解决缩进错误） + 代码生成优化（统一导入格式） + v2.13 功能全保留（药瓶机制重构 + 装备掉落优化 + 跨平台部署支持 + 本地调试体验改进 + 无用代码清理）*

