-- 塔爬游戏数据库表结构创建脚本
-- MySQL版本
-- 包含完整的表注释和字段注释

-- 玩家表 - 存储玩家基本信息、属性和状态
CREATE TABLE IF NOT EXISTS players (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '玩家唯一标识ID',
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '玩家名称，必须唯一',
    password VARCHAR(255) DEFAULT 'default' COMMENT '玩家登录密码',
    health INT NOT NULL DEFAULT 100 COMMENT '玩家当前生命值',
    max_health INT NOT NULL DEFAULT 100 COMMENT '玩家最大生命值',
    mana INT NOT NULL DEFAULT 50 COMMENT '玩家当前法力值',
    max_mana INT NOT NULL DEFAULT 50 COMMENT '玩家最大法力值',
    gold INT NOT NULL DEFAULT 0 COMMENT '玩家持有金币数量',
    attack INT NOT NULL DEFAULT 10 COMMENT '玩家基础攻击力',
    defense INT NOT NULL DEFAULT 5 COMMENT '玩家基础防御力',
    level INT NOT NULL DEFAULT 1 COMMENT '玩家等级',
    experience INT NOT NULL DEFAULT 0 COMMENT '玩家经验值',
    position_x INT NOT NULL DEFAULT 0 COMMENT '玩家在楼层中的X坐标',
    position_y INT NOT NULL DEFAULT 0 COMMENT '玩家在楼层中的Y坐标',
    floor_level INT NOT NULL DEFAULT 1 COMMENT '玩家所在楼层',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '玩家是否处于活跃状态',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '玩家创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '玩家信息最后更新时间',

    INDEX idx_players_name (name),
    INDEX idx_players_active (is_active),
    INDEX idx_players_floor (floor_level)
) COMMENT='玩家基本信息表';

-- 武器属性表 - 存储武器锻造的额外属性
CREATE TABLE IF NOT EXISTS weapon_attributes (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '武器属性唯一标识ID',
    player_id INT NOT NULL COMMENT '所属玩家ID',
    attribute_name VARCHAR(50) NOT NULL COMMENT '属性名称(如：暴击率、吸血等)',
    attribute_value INT NOT NULL DEFAULT 0 COMMENT '属性值',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '属性创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '属性更新时间',

    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    INDEX idx_weapon_attributes_player (player_id),
    INDEX idx_weapon_attributes_name (attribute_name)
) COMMENT='武器属性表';

-- 游戏存档表 - 存储玩家的游戏存档
CREATE TABLE IF NOT EXISTS game_saves (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '存档唯一标识ID',
    player_id INT NOT NULL COMMENT '所属玩家ID',
    floor_level INT NOT NULL DEFAULT 1 COMMENT '存档时所在楼层',
    save_name VARCHAR(200) NOT NULL COMMENT '存档名称',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否为当前激活存档',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '存档创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '存档更新时间',

    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    INDEX idx_saves_player (player_id),
    INDEX idx_saves_active (is_active),
    INDEX idx_saves_floor (floor_level)
) COMMENT='游戏存档表';

-- 保存的楼层表 - 存储每个存档的楼层地图数据
CREATE TABLE IF NOT EXISTS saved_floors (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '楼层唯一标识ID',
    save_id INT NOT NULL COMMENT '所属存档ID',
    floor_level INT NOT NULL COMMENT '楼层编号',
    width INT NOT NULL DEFAULT 15 COMMENT '楼层宽度',
    height INT NOT NULL DEFAULT 15 COMMENT '楼层高度',
    player_start_x INT NOT NULL DEFAULT 7 COMMENT '玩家起始X坐标',
    player_start_y INT NOT NULL DEFAULT 7 COMMENT '玩家起始Y坐标',
    stairs_x INT NOT NULL DEFAULT 0 COMMENT '楼梯X坐标',
    stairs_y INT NOT NULL DEFAULT 0 COMMENT '楼梯Y坐标',
    is_merchant_floor BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否为商人楼层',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '楼层创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '楼层更新时间',

    FOREIGN KEY (save_id) REFERENCES game_saves(id) ON DELETE CASCADE,
    INDEX idx_floors_save (save_id),
    INDEX idx_floors_level (floor_level),
    INDEX idx_floors_merchant (is_merchant_floor)
) COMMENT='保存的楼层表';

-- 楼层物品表 - 存储楼层上的物品和药水
CREATE TABLE IF NOT EXISTS floor_items (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '物品唯一标识ID',
    floor_id INT NOT NULL COMMENT '所属楼层ID',
    item_type VARCHAR(50) NOT NULL DEFAULT 'item' COMMENT '物品类型(item/potion)',
    item_name VARCHAR(100) NOT NULL COMMENT '物品名称',
    symbol VARCHAR(10) NOT NULL DEFAULT '+' COMMENT '物品显示符号',
    effect_type VARCHAR(50) NOT NULL DEFAULT '' COMMENT '效果类型(heal/mana等)',
    effect_value INT NOT NULL DEFAULT 0 COMMENT '效果数值',
    position_x INT NOT NULL DEFAULT 0 COMMENT '物品X坐标',
    position_y INT NOT NULL DEFAULT 0 COMMENT '物品Y坐标',
    rarity_level VARCHAR(20) NOT NULL DEFAULT 'common' COMMENT '稀有度等级',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '物品创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '物品更新时间',

    FOREIGN KEY (floor_id) REFERENCES saved_floors(id) ON DELETE CASCADE,
    INDEX idx_items_floor (floor_id),
    INDEX idx_items_position (floor_id, position_x, position_y),
    INDEX idx_items_type (item_type),
    INDEX idx_items_rarity (rarity_level)
) COMMENT='楼层物品表';

-- 玩家装备表 - 存储玩家拥有的装备
CREATE TABLE IF NOT EXISTS player_equipment (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '装备唯一标识ID',
    player_id INT NOT NULL COMMENT '所属玩家ID',
    equipment_type VARCHAR(50) NOT NULL COMMENT '装备类型(weapon/armor等)',
    item_name VARCHAR(100) NOT NULL COMMENT '装备名称',
    attack_value INT NOT NULL DEFAULT 0 COMMENT '攻击力加成',
    defense_value INT NOT NULL DEFAULT 0 COMMENT '防御力加成',
    rarity_level VARCHAR(20) NOT NULL DEFAULT 'common' COMMENT '稀有度等级',
    is_equipped BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否已装备',
    slot_position INT NOT NULL DEFAULT 1 COMMENT '装备槽位置',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '装备获取时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '装备更新时间',

    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    INDEX idx_equipment_player (player_id),
    INDEX idx_equipment_type (equipment_type),
    INDEX idx_equipment_equipped (is_equipped)
) COMMENT='玩家装备表';

-- 楼层商人表 - 存储楼层的商人信息
CREATE TABLE IF NOT EXISTS floor_merchants (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '商人唯一标识ID',
    floor_id INT NOT NULL COMMENT '所属楼层ID',
    merchant_name VARCHAR(100) NOT NULL COMMENT '商人名称',
    merchant_type VARCHAR(50) NOT NULL DEFAULT 'general' COMMENT '商人类型(general/equipment等)',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT '商人是否激活',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '商人创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '商人更新时间',

    FOREIGN KEY (floor_id) REFERENCES saved_floors(id) ON DELETE CASCADE,
    INDEX idx_merchants_floor (floor_id),
    INDEX idx_merchants_active (is_active),
    INDEX idx_merchants_type (merchant_type)
) COMMENT='楼层商人表';

-- 商人库存表 - 存储商人的可售物品
CREATE TABLE IF NOT EXISTS merchant_inventories (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '库存物品唯一标识ID',
    merchant_id INT NOT NULL COMMENT '所属商人ID',
    item_name VARCHAR(100) NOT NULL COMMENT '物品名称',
    item_type VARCHAR(50) NOT NULL DEFAULT 'item' COMMENT '物品类型(weapon/potion/item)',
    quantity INT NOT NULL DEFAULT 1 COMMENT '库存数量',
    price INT NOT NULL DEFAULT 10 COMMENT '物品售价',
    rarity_level VARCHAR(20) NOT NULL DEFAULT 'common' COMMENT '稀有度等级',
    effect_type VARCHAR(50) NOT NULL DEFAULT '' COMMENT '效果类型',
    effect_value INT NOT NULL DEFAULT 0 COMMENT '效果数值',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '库存创建时间',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '库存更新时间',

    FOREIGN KEY (merchant_id) REFERENCES floor_merchants(id) ON DELETE CASCADE,
    INDEX idx_inventory_merchant (merchant_id),
    INDEX idx_inventory_type (item_type),
    INDEX idx_inventory_rarity (rarity_level),
    INDEX idx_inventory_quantity (quantity)
) COMMENT='商人库存表';

-- 插入测试数据
INSERT IGNORE INTO players (name, password, health, max_health, mana, max_mana, gold, attack, defense, level, experience) VALUES
('admin', 'admin123', 150, 150, 100, 100, 1000, 25, 15, 5, 1000);

-- 显示所有表
SHOW TABLES;