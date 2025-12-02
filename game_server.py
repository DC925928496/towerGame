import asyncio
import json
import logging
import websockets
from typing import Dict, List, Optional
from dataclasses import asdict

from map_generator import generate_floor
from game_model import Player, Floor, Position, CellType, Item, WeaponAttribute
from game_logic import (
    move_player, pickup_item, player_attack,
    handle_trade_request, get_merchant_info,
    forge_weapon_attribute, get_forge_info
)
from services import service_manager
from config.database_config import config_manager
from database.dao import dao_manager


logger = logging.getLogger(__name__)


class GameState:
    """游戏状态管理"""
    def __init__(self):
        self.player: Optional[Player] = None
        self.current_floor: Optional[Floor] = None
        self.floor_level: int = 1
        self.game_over: bool = False
        self.game_over_reason: str = ""
        self.merchant_attempt_count: int = 0  # 商人楼层尝试计数器
        self.player_id: Optional[int] = None
        self.save_id: Optional[int] = None
        self.db_enabled: bool = False
        self.session_token: Optional[str] = None
        self.authenticated_user: Optional[Dict] = None
        self.is_authenticated: bool = False

        # 尝试初始化数据库连接
        try:
            if config_manager.is_configured():
                self.db_enabled = True
            else:
                self.db_enabled = False
        except Exception as e:
            self.db_enabled = False

    def new_game(self):
        """开始新游戏"""
        # 如果已登录，保持用户ID，否则重置
        original_player_id = self.player_id
        original_auth_user = self.authenticated_user
        original_session_token = self.session_token
        original_is_authenticated = self.is_authenticated

        self.player = Player()
        self.floor_level = 1
        self.game_over = False
        self.game_over_reason = ""
        self.merchant_attempt_count = 0  # 重置商人楼层尝试计数器
        self.save_id = None   # 重置存档ID

        # 保持登录状态
        self.player_id = original_player_id
        self.authenticated_user = original_auth_user
        self.session_token = original_session_token
        self.is_authenticated = original_is_authenticated

        # 生成第一层
        self.current_floor = generate_floor(1, None, self.merchant_attempt_count)
        self.player.position = self.current_floor.player_start_pos

        # 第一层不需要更新商人计数器（不是每10层的候选）

        return self.get_initial_messages()

    def get_initial_messages(self) -> List[Dict]:
        """获取初始消息（地图、玩家信息）"""
        messages = []

        # 发送地图
        messages.append({
            'type': 'map',
            'grid': self.current_floor.to_serializable_grid(self.player)
        })

        # 发送玩家信息
        messages.append(self.get_player_info_message())

        # 发送欢迎日志
        messages.append({
            'type': 'log',
            'message': f'欢迎来到爬塔游戏！目标：爬到第100层并击败最终Boss！'
        })

        return messages

    def get_player_info_message(self) -> Dict:
        """获取玩家信息消息"""
        return {
            'type': 'info',
            'hp': self.player.hp,
            'max_hp': self.player.max_hp,
            'attack': self.player.attack,
            'weapon_atk': self.player.weapon_atk,
            'defense': self.player.defense,
            'armor_def': self.player.armor_def,
            'total_atk': self.player.total_atk,
            'total_def': self.player.total_def,
            'exp': self.player.exp,
            'exp_needed': self.player.exp_needed,
            'level': self.player.level,
            'gold': self.player.gold,
            'floor': self.floor_level,
            'inventory': self.player.get_inventory_list(),
            'weapon_name': self.player.weapon_name,
            'weapon_rarity': self.player.weapon_rarity,
            'weapon_attributes': [attr.to_dict() for attr in self.player.weapon_attributes],
            'armor_name': self.player.armor_name
        }

    def _clear_runtime_state(self):
        """清理当前运行时的游戏状态"""
        self.player = None
        self.current_floor = None
        self.floor_level = 1
        self.game_over = False
        self.game_over_reason = ""
        self.merchant_attempt_count = 0
        self.save_id = None

    def _cleanup_save_data(self):
        """删除当前玩家的存档数据（数据库或本地），忽略错误"""
        if self.db_enabled and self.player_id:
            try:
                target_save_id = self.save_id
                if not target_save_id:
                    latest_save = service_manager.game_save.get_latest_save(self.player_id)
                    if latest_save:
                        target_save_id = latest_save.get('id')

                if target_save_id:
                    service_manager.game_save.delete_save(target_save_id)
            except Exception as e:
                logger.warning(f"删除数据库存档失败: {e}")
        else:
            try:
                from save_load import delete_save
                delete_save()
            except Exception as e:
                logger.warning(f"删除本地存档失败: {e}")

        self.save_id = None

    def _finalize_game_over(self, reason: str, cleanup_save: bool = False) -> List[Dict]:
        """统一处理游戏结束逻辑"""
        self.game_over = True
        self.game_over_reason = reason

        if cleanup_save:
            self._cleanup_save_data()

        return [{
            'type': 'gameover',
            'reason': reason,
            'final_floor': self.floor_level
        }]

    def move(self, direction: str) -> List[Dict]:
        """处理移动命令"""
        if self.game_over:
            return [{'type': 'log', 'message': '游戏已结束！'}]

        messages = []

        # 移动
        result = move_player(self.player, direction, self.current_floor)

        if result['logs']:
            messages.append({'type': 'log', 'message': result['logs'][0]})

        # 检查游戏结束
        if not self.player.is_alive():
            messages.extend(self._finalize_game_over("死亡", cleanup_save=True))
            return messages

        # 如果有战斗
        if result['bumped_into'] == 'monster':
            monster = result['monster']
            combat_messages = self.handle_combat(monster)
            messages.extend(combat_messages)

            # 检查是否击败最终Boss
            if self.floor_level == 100:
                boss_id = list(self.current_floor.monsters.keys())[0]
                boss = self.current_floor.monsters[boss_id]
                if not boss.is_alive():
                    self.game_over = True
                    self.game_over_reason = "通关成功！你击败了死亡骑士！"
                    messages.append({
                        'type': 'gameover',
                        'reason': self.game_over_reason,
                        'final_floor': self.floor_level
                    })

            return messages

        # 如果成功移动
        if result['success']:
            # 处理自动交互（拾取道具、上楼）
            if 'auto_interactions' in result and result['auto_interactions']:
                messages.extend(result['auto_interactions'])

                # 检查是否有楼层变化（自动上楼）
                for msg in result['auto_interactions']:
                    if msg.get('type') == 'auto_descend' and msg.get('floor'):
                        # 自动上楼成功，需要重新生成楼层
                        self.floor_level += 1
                        prev_floor = self.current_floor
                        self.current_floor = generate_floor(self.floor_level, prev_floor, self.merchant_attempt_count)
                        self.player.position = self.current_floor.player_start_pos

                        # 更新商人楼层尝试计数器（使用旧的楼层级别）
                        self.update_merchant_attempt_count(self.current_floor, self.floor_level - 1)

                        # 自动上楼后自动保存
                        self.auto_save()

                        # 发送新楼层地图
                        messages.append({
                            'type': 'map',
                            'grid': self.current_floor.to_serializable_grid(self.player)
                        })
                        messages.append(self.get_player_info_message())
                        return messages

            # 更新地图
            messages.append({
                'type': 'map',
                'grid': self.current_floor.to_serializable_grid(self.player)
            })

            # 更新玩家信息
            messages.append(self.get_player_info_message())

        # 如果撞到墙，也更新地图（显示玩家位置）
        elif result['bumped_into'] == 'wall':
            messages.append({
                'type': 'map',
                'grid': self.current_floor.to_serializable_grid(self.player)
            })
            messages.append(self.get_player_info_message())

        return messages

    def handle_combat(self, monster) -> List[Dict]:
        """处理战斗"""
        messages = []

        # 玩家攻击
        combat_result = player_attack(self.player, monster, self.current_floor)

        # 发送战斗日志
        for log in combat_result['logs']:
            messages.append({'type': 'log', 'message': log})

        # 发送战斗信息
        messages.append({
            'type': 'combat',
            'player_damage': combat_result['player_damage'],
            'monster_damage': combat_result['monster_damage'],
            'monster_hp': monster.hp if monster.is_alive() else 0,
            'monster_max_hp': monster.max_hp,
            'monster_name': monster.name,
            'monster_dead': combat_result['monster_dead'],
            'exp_gained': combat_result['exp_gained'],
            'gold_gained': combat_result['gold_gained']
        })

        # 检查玩家死亡
        if not self.player.is_alive():
            messages.extend(self._finalize_game_over(f"被{monster.name}击败", cleanup_save=True))
            return messages

        # 无论怪物是否死亡，都更新玩家信息（实时显示属性变化）
        messages.append(self.get_player_info_message())

        # 如果怪物死亡，额外更新地图（移除怪物）
        if combat_result['monster_dead']:
            # 更新地图（移除怪物）
            messages.append({
                'type': 'map',
                'grid': self.current_floor.to_serializable_grid(self.player)
            })

        return messages

    def pickup(self) -> List[Dict]:
        """处理拾取命令"""
        if self.game_over:
            return [{'type': 'log', 'message': '游戏已结束！'}]

        messages = []

        result = pickup_item(self.player, self.current_floor)

        if result['logs']:
            messages.append({'type': 'log', 'message': result['logs'][0]})

        if result['success']:
            # 更新地图（移除道具）
            messages.append({
                'type': 'map',
                'grid': self.current_floor.to_serializable_grid(self.player)
            })

            # 更新玩家信息
            messages.append(self.get_player_info_message())

        return messages

    def use_item(self, item_name: str) -> List[Dict]:
        """处理使用道具命令"""
        if self.game_over:
            return [{'type': 'log', 'message': '游戏已结束！'}]

        messages = []

        log_message = self.player.use_item(item_name)

        if log_message:
            messages.append({'type': 'log', 'message': log_message})
            messages.append(self.get_player_info_message())

            # 检查玩家死亡（虽然使用血瓶不会导致死亡，但保留检查）
            if not self.player.is_alive():
                messages.extend(self._finalize_game_over("死亡", cleanup_save=True))

        return messages

    
    def update_merchant_attempt_count(self, new_floor: Floor, previous_level: int):
        """更新商人楼层尝试计数器"""
        if new_floor.is_merchant_floor:
            # 触发了商人楼层，重置计数器
            self.merchant_attempt_count = 0
        elif previous_level > 10 and previous_level % 10 == 0 and previous_level < 100:
            # 是候选楼层（第20,30,40...）但没有触发，增加计数器
            self.merchant_attempt_count += 1

    def merchant_info(self) -> List[Dict]:
        """处理获取商人信息命令"""
        if self.game_over:
            return [{'type': 'log', 'message': '游戏已结束！'}]

        response = get_merchant_info(self.player, self.current_floor)
        return [{'type': 'merchant_info', **response}]

    def forge_info(self) -> List[Dict]:
        """处理获取锻造信息命令"""
        if self.game_over:
            return [{'type': 'log', 'message': '游戏已结束！'}]

        response = get_forge_info(self.player)
        return [{'type': 'forge_info', **response}]

    def forge(self, attribute_index: int) -> List[Dict]:
        """处理锻造命令"""
        if self.game_over:
            return [{'type': 'log', 'message': '游戏已结束！'}]

        messages = []

        result = forge_weapon_attribute(self.player, attribute_index)

        if result['success']:
            messages.append({
                'type': 'forge_success',
                'message': result['message'],
                'attribute_index': result['attribute_index'],
                'new_level': result['new_level'],
                'gold_spent': result['gold_spent']
            })
        elif result.get('is_forge_failure'):
            # 锻造失败（非错误情况）
            messages.append({
                'type': 'forge_failure',
                'message': result['message'],
                'attribute_index': result['attribute_index'],
                'current_level': result['current_level'],
                'gold_spent': result['gold_spent']
            })
        else:
            # 锻造错误（金币不足等）
            messages.append({
                'type': 'forge_error',
                'message': result['message']
            })

        # 无论成功失败都更新玩家信息
        messages.append(self.get_player_info_message())
        return messages

    def suicide(self) -> List[Dict]:
        """重置游戏状态并删除存档（用于自杀重启）"""
        messages = []

        try:
            # 删除当前存档
            self._cleanup_save_data()

            # 清理并重新开始游戏
            self._clear_runtime_state()

            # 开始新游戏
            messages = self.new_game()
            messages.append({
                'type': 'log',
                'message': '游戏已自杀重启！'
            })

        except Exception as e:
            messages.append({
                'type': 'error',
                'message': f'自杀重启失败: {str(e)}'
            })

        return messages

    def trade(self, item_name: str) -> List[Dict]:
        """处理购买命令"""
        if self.game_over:
            return [{'type': 'log', 'message': '游戏已结束！'}]

        messages = []

        result = handle_trade_request(self.player, self.current_floor, item_name)

        if result['success']:
            messages.append({
                'type': 'trade_success',
                'message': result['message'],
                'new_gold': result['new_gold'],
                'item': {
                    'name': result['item'].name,
                    'type': result['item'].effect_type,
                    'value': result['item'].effect_value,
                    'price': result['item'].price
                }
            })
            # 发送更新后的玩家信息
            messages.append(self.get_player_info_message())
        else:
            messages.append({
                'type': 'trade_failed',
                'message': result['message']
            })

        return messages

    def save_game(self) -> bool:
        """保存游戏状态到数据库"""
        if not self.db_enabled or not self.player or not self.player_id:
            return False

        try:
            # 更新玩家信息（玩家记录应该已经存在）
            player_data = {
                'hp': self.player.hp,
                'max_hp': self.player.max_hp,
                'attack': self.player.attack,
                'defense': self.player.defense,
                'exp': self.player.exp,
                'level': self.player.level,
                'gold': self.player.gold,
                'position_x': self.player.position.x if self.player.position else 0,
                'position_y': self.player.position.y if self.player.position else 0,
                'floor_level': self.floor_level
            }
            updated = service_manager.player.update_player(self.player_id, player_data)
            if not updated:
                raise RuntimeError("更新玩家信息失败")

            # 保存装备信息
            self._save_equipment()

            # 保存武器词条
            self._save_weapon_attributes()

            # 保存道具信息
            self._save_inventory()

            # 保存游戏状态（覆盖最新存档或创建新存档）
            self._save_game_state()

            return True
        except Exception as e:
            return False

    def auto_save(self):
        """自动保存游戏（在关键事件后调用）"""
        if self.db_enabled:
            asyncio.create_task(asyncio.to_thread(self.save_game))

    def _save_game_state(self):
        """保存游戏状态，优先更新最新存档"""
        try:
            # 尝试获取最新存档
            latest_save = service_manager.game_save.get_latest_save(self.player_id)

            if latest_save:
                # 更新现有存档
                update_data = {
                    'floor_level': self.floor_level,
                    'save_name': f"自动保存 - 第{self.floor_level}层",
                    'is_active': True
                }
                success = service_manager.game_save.update_save(latest_save['id'], update_data)
                if success:
                    self.save_id = latest_save['id']
                else:
                    raise RuntimeError("更新存档失败")
            else:
                # 创建新存档
                self.save_id = service_manager.game_save.create_save(
                    self.player_id,
                    self.floor_level,
                    f"自动保存 - 第{self.floor_level}层"
                )

        except Exception as e:
            # 如果更新失败，创建新存档作为备选
            self.save_id = service_manager.game_save.create_save(
                self.player_id,
                self.floor_level,
                f"紧急保存 - 第{self.floor_level}层"
            )

    def load_latest_save(self) -> bool:
        """加载用户最新存档"""
        if not self.db_enabled or not self.player_id:
            return False

        try:
            # 获取用户最新存档
            saves = service_manager.game_save.get_player_saves(self.player_id)
            if not saves:
                return False

            # 获取最新存档
            latest_save = max(saves, key=lambda x: x.get('created_at', ''))
            save_id = latest_save['id']
            floor_level = latest_save.get('floor_level', 1)

            # 从数据库加载玩家数据
            player_info = service_manager.player.get_by_id(self.player_id)
            if not player_info:
                return False

            # 初始化玩家对象
            self.player = Player()
            self.floor_level = floor_level
            self.save_id = save_id

            # 加载玩家属性
            self.player.hp = player_info.get('hp', 500)
            self.player.max_hp = player_info.get('max_hp', 500)
            self.player.attack = player_info.get('attack', 50)
            self.player.defense = player_info.get('defense', 20)
            self.player.exp = player_info.get('exp', 0)
            self.player.level = player_info.get('level', 1)
            self.player.gold = player_info.get('gold', 0)

            # 设置玩家位置
            position_x = player_info.get('position_x', 0)
            position_y = player_info.get('position_y', 0)
            self.player.position = Position(position_x, position_y)

            # 经验需求会通过exp_needed属性自动计算，无需手动调用

            # 加载装备信息
            self._load_equipment()

            # 加载道具信息
            self._load_inventory()

            # 生成对应楼层
            self.current_floor = generate_floor(self.floor_level, None, self.merchant_attempt_count)

            # 如果玩家位置有效，设置玩家位置
            if (0 <= position_x < len(self.current_floor.grid) and
                0 <= position_y < len(self.current_floor.grid[0])):
                self.player.position = Position(position_x, position_y)
            else:
                # 如果位置无效，使用默认起始位置
                self.player.position = self.current_floor.player_start_pos

            return True

        except Exception as e:
            return False

    def _load_equipment(self):
        """加载玩家装备信息"""
        try:
            equipment_list = service_manager.equipment.get_player_equipment(self.player_id)

            for equipment in equipment_list:
                if equipment['is_equipped']:
                    equipment_type = equipment['equipment_type']
                    item_name = equipment['item_name']
                    attack_value = equipment['attack_value']
                    defense_value = equipment['defense_value']
                    rarity_level = equipment['rarity_level']

                    if equipment_type == 'weapon':
                        # 加载武器
                        self.player.weapon_name = item_name
                        self.player.weapon_atk = attack_value
                        self.player.weapon_rarity = rarity_level

                        # 加载武器词条
                        self._load_weapon_attributes()

                    elif equipment_type == 'armor':
                        # 加载防具
                        self.player.armor_name = item_name
                        self.player.armor_def = defense_value

        except Exception as e:
            pass

    def _load_weapon_attributes(self):
        """加载武器词条"""
        try:
            # 从数据库获取玩家的武器词条
            weapon_attrs_data = dao_manager.weapon_attribute.get_by_player_id(self.player_id)

            # 清空现有词条
            self.player.weapon_attributes = []

            # 转换为WeaponAttribute对象
            for attr_data in weapon_attrs_data:
                weapon_attr = WeaponAttribute(
                    attribute_type=attr_data['attribute_type'],
                    value=attr_data['value'],
                    description=attr_data['description'],
                    level=attr_data.get('level', 0)
                )
                self.player.weapon_attributes.append(weapon_attr)

        except Exception as e:
            self.player.weapon_attributes = []

    def _load_inventory(self):
        """加载玩家道具信息"""
        try:
            inventory_list = service_manager.inventory.get_player_inventory(self.player_id)

            # 将inventory设置为字典格式 {道具名: 数量}
            self.player.inventory = {}

            for item in inventory_list:
                item_name = item['item_name']
                quantity = item['quantity']
                self.player.inventory[item_name] = quantity

        except Exception as e:
            pass

    def _save_weapon_attributes(self):
        """保存武器词条"""
        try:
            # 先删除现有的武器词条
            dao_manager.weapon_attribute.delete_by_player_id(self.player_id)

            # 如果有武器词条，保存到数据库
            if self.player.weapon_attributes:
                attrs_data = []
                for attr in self.player.weapon_attributes:
                    attrs_data.append({
                        'attribute_type': attr.attribute_type,
                        'value': attr.value,
                        'description': attr.description,
                        'level': attr.level
                    })

                dao_manager.weapon_attribute.create_player_attributes(self.player_id, attrs_data)

        except Exception as e:
            pass

    def _save_equipment(self):
        """保存玩家装备信息"""
        try:
            # 先清除现有的已装备状态
            service_manager.equipment.unequip_item(self.player_id, 'weapon')
            service_manager.equipment.unequip_item(self.player_id, 'armor')

            # 保存当前装备的武器
            if self.player.weapon_name:
                service_manager.equipment.save_equipment(
                    player_id=self.player_id,
                    equipment_type='weapon',
                    item_name=self.player.weapon_name,
                    attack_value=self.player.weapon_atk,
                    rarity_level=self.player.weapon_rarity or 'common'
                )

            # 保存当前装备的防具
            if self.player.armor_name:
                service_manager.equipment.save_equipment(
                    player_id=self.player_id,
                    equipment_type='armor',
                    item_name=self.player.armor_name,
                    defense_value=self.player.armor_def,
                    rarity_level='common'  # 防具稀有度暂时使用默认值
                )

        except Exception as e:
            pass

    def _save_inventory(self):
        """保存玩家道具信息"""
        try:
            # 先清空现有道具
            service_manager.inventory.clear_inventory(self.player_id)

            # 直接从字典保存道具
            for item_name, quantity in self.player.inventory.items():
                if quantity > 0:
                    service_manager.inventory.add_item(self.player_id, item_name, quantity)

            total_items = sum(self.player.inventory.values())

        except Exception as e:
            pass


async def handle_auth_message(websocket, data: Dict, game: GameState, session_id: str):
    """处理认证消息"""
    action = data.get('action')

    try:
        if action == 'login':
            await handle_login(websocket, data, game, session_id)
        elif action == 'register':
            await handle_register(websocket, data, game)
        elif action == 'verify_token':
            await handle_token_verify(websocket, data, game, session_id)
        elif action == 'logout':
            await handle_logout(websocket, data, game, session_id)
        else:
            await websocket.send(json.dumps({
                'type': 'auth_error',
                'message': '无效的认证操作'
            }))
    except Exception as e:
        await websocket.send(json.dumps({
            'type': 'auth_error',
            'message': f'认证处理失败: {str(e)}'
        }))


async def handle_login(websocket, data: Dict, game: GameState, session_id: str):
    """处理用户登录"""
    username = data.get('username')
    password = data.get('password')

    try:
        # 获取客户端信息
        ip_address = websocket.remote_address[0] if websocket.remote_address else None
        user_agent = websocket.request_headers.get('User-Agent', '') if hasattr(websocket, 'request_headers') else ''

        # 调用认证服务
        auth_result = service_manager.auth.authenticate_user(
            username, password, ip_address, user_agent
        )

        if auth_result['success']:
            # 设置游戏状态
            game.is_authenticated = True
            game.authenticated_user = auth_result['data']
            game.session_token = auth_result['data']['session_token']
            game.player_id = auth_result['data']['player_id']

            # 发送登录成功消息
            await websocket.send(json.dumps({
                'type': 'auth_success',
                'user_info': {
                    'username': auth_result['data']['username'],
                    'player_id': auth_result['data']['player_id'],
                    'nickname': auth_result['data'].get('nickname', 'gamer'),
                    'session_token': game.session_token,  # 添加session_token
                    'level': auth_result['data'].get('level', 1),
                    'experience': auth_result['data'].get('experience', 0),
                    'gold': auth_result['data'].get('gold', 0)
                }
            }))

            # 检查是否有存档并开始游戏
            await start_game_for_user(websocket, game)

        else:
            await websocket.send(json.dumps({
                'type': 'auth_error',
                'message': auth_result.get('error', '登录失败')
            }))

    except ValueError as e:
        await websocket.send(json.dumps({
            'type': 'auth_error',
            'message': str(e)
        }))
    except Exception as e:
        await websocket.send(json.dumps({
            'type': 'auth_error',
            'message': '登录失败，请稍后重试'
        }))


async def handle_register(websocket, data: Dict, game: GameState):
    """处理用户注册"""
    username = data.get('username')
    password = data.get('password')
    nickname = data.get('nickname', '')

    try:
        # 调用认证服务
        register_result = service_manager.auth.register_user(username, password, nickname)

        if register_result['success']:
            await websocket.send(json.dumps({
                'type': 'register_success',
                'message': '注册成功！正在自动登录...'
            }))

        else:
            await websocket.send(json.dumps({
                'type': 'register_error',
                'message': register_result.get('error', '注册失败')
            }))

    except ValueError as e:
        await websocket.send(json.dumps({
            'type': 'register_error',
            'message': str(e)
        }))
    except Exception as e:
        await websocket.send(json.dumps({
            'type': 'register_error',
            'message': '注册失败，请稍后重试'
        }))


async def handle_token_verify(websocket, data: Dict, game: GameState, session_id: str):
    """处理token验证"""
    session_token = data.get('session_token')

    try:
        # 验证会话token
        session_info = service_manager.auth.validate_session(session_token, session_id)

        if session_info:
            # 获取用户信息
            player_info = service_manager.player.get_by_id(session_info['player_id'])
            if player_info:
                # 设置游戏状态
                game.is_authenticated = True
                game.player_id = player_info['id']
                game.session_token = session_token
                game.authenticated_user = {
                    'player_id': player_info['id'],
                    'username': player_info['name'],
                    'nickname': player_info.get('nickname')
                }

                # 发送验证成功消息
                await websocket.send(json.dumps({
                    'type': 'auth_success',
                    'user_info': {
                        'player_id': player_info['id'],
                        'username': player_info['name'],
                        'nickname': player_info.get('nickname'),
                        'session_token': session_token
                    }
                }))

                # 启动游戏
                await start_game_for_user(websocket, game)
            else:
                await websocket.send(json.dumps({
                    'type': 'auth_error',
                    'message': '用户信息不存在'
                }))
        else:
            await websocket.send(json.dumps({
                'type': 'auth_error',
                'message': 'Token验证失败或已过期'
            }))

    except Exception as e:
        await websocket.send(json.dumps({
            'type': 'auth_error',
            'message': 'Token验证失败'
        }))


async def handle_logout(websocket, data: Dict, game: GameState, session_id: str):
    """处理用户登出"""
    try:
        # 重置游戏状态
        game.is_authenticated = False
        game.current_user_id = None
        game.player_info = None
        game.current_grid = None

        # 清理会话（可选）
        # 这里可以添加服务端的会话清理逻辑

        await websocket.send(json.dumps({
            'type': 'logout_success',
            'message': '登出成功'
        }))

    except Exception as e:
        await websocket.send(json.dumps({
            'type': 'auth_error',
            'message': '登出失败'
        }))


async def handle_nickname_update(websocket, data: Dict, game: GameState):
    """处理昵称更新请求"""
    new_nickname = data.get('nickname', '').strip()

    try:
        # 验证输入
        if not new_nickname:
            await websocket.send(json.dumps({
                'type': 'nickname_update_error',
                'message': '昵称不能为空'
            }))
            return

        if len(new_nickname) > 50:
            await websocket.send(json.dumps({
                'type': 'nickname_update_error',
                'message': '昵称长度不能超过50个字符'
            }))
            return

        # 调用认证服务更新昵称
        update_result = service_manager.auth.update_nickname(game.player_id, new_nickname)

        if update_result['success']:
            # 更新游戏中的用户信息
            if hasattr(game, 'user_info'):
                game.user_info['nickname'] = new_nickname

            await websocket.send(json.dumps({
                'type': 'nickname_update_success',
                'nickname': new_nickname
            }))

        else:
            await websocket.send(json.dumps({
                'type': 'nickname_update_error',
                'message': update_result.get('error', '昵称更新失败')
            }))

    except ValueError as e:
        await websocket.send(json.dumps({
            'type': 'nickname_update_error',
            'message': str(e)
        }))
    except Exception as e:
        await websocket.send(json.dumps({
            'type': 'nickname_update_error',
            'message': '昵称更新失败，请稍后重试'
        }))


async def start_game_for_user(websocket, game: GameState):
    """为已登录用户开始游戏"""
    try:
        # 如果启用了数据库，尝试加载用户的存档
        save_loaded = False
        if game.db_enabled and game.player_id:
            save_loaded = game.load_latest_save()
            if save_loaded:
                await websocket.send(json.dumps({
                    'type': 'log',
                    'message': f'已加载存档，当前楼层: {game.floor_level}'
                }))

        if save_loaded:
            # 如果成功加载存档，发送加载后的游戏状态
            initial_messages = []

            # 发送地图
            initial_messages.append({
                'type': 'map',
                'grid': game.current_floor.to_serializable_grid(game.player)
            })

            # 发送玩家信息
            initial_messages.append(game.get_player_info_message())

            # 发送欢迎日志
            initial_messages.append({
                'type': 'log',
                'message': f'欢迎回到爬塔游戏！当前在第{game.floor_level}层，目标：爬到第100层并击败最终Boss！'
            })
        else:
            # 开始新游戏（会保持登录状态）
            initial_messages = game.new_game()

        # 发送初始游戏状态
        for msg in initial_messages:
            await websocket.send(json.dumps(msg))

        # 如果成功加载了存档，发送额外信息
        if save_loaded:
            await websocket.send(json.dumps({
                'type': 'log',
                'message': '游戏进度已恢复'
            }))

    except Exception as e:
        await websocket.send(json.dumps({
            'type': 'auth_error',
            'message': '游戏启动失败，请重新登录'
        }))


async def handle_suicide(websocket, data: Dict, game: GameState):
    """处理自杀重启请求"""
    try:
        # 检查用户是否已认证
        if not game.authenticated_user:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': '请先登录'
            }))
            return

        # 删除用户的存档（如果有）
        user_id = game.authenticated_user['player_id']
        if game.db_enabled and user_id and game.save_id:
            # 删除数据库存档
            try:
                service_manager.game_save_service.delete_save(game.save_id)
            except ValueError:
                pass  # 存档不存在，忽略
            game.save_id = None
        else:
            # 删除本地存档
            from save_load import delete_save
            delete_save()

        # 立即触发游戏结束（就像死亡一样）
        game.game_over = True
        game.game_over_reason = "自杀重启"

        # 发送游戏结束消息
        await websocket.send(json.dumps({
            'type': 'gameover',
            'reason': game.game_over_reason,
            'final_floor': game.floor_level
        }))

    except Exception as e:
        await websocket.send(json.dumps({
            'type': 'error',
            'message': f'自杀重启失败: {str(e)}'
        }))


# 全局游戏状态存储
# key: session_id, value: GameState
games: Dict[str, GameState] = {}


async def handle_client(websocket):
    """处理WebSocket客户端连接"""
    session_id = str(id(websocket))
    game = GameState()
    games[session_id] = game

    try:
        # 等待认证消息
        await websocket.send(json.dumps({
            'type': 'log',
            'message': '请先登录或注册账户'
        }))

        # 认证状态
        is_authenticated = False

        # 处理消息
        async for message in websocket:
            try:
                data = json.loads(message)

                # 处理认证消息
                if data.get('type') == 'auth':
                    await handle_auth_message(websocket, data, game, session_id)
                    continue

                # 检查是否已认证
                if not game.authenticated_user:
                    await websocket.send(json.dumps({
                        'type': 'auth_error',
                        'message': '请先进行身份认证'
                    }))
                    continue

                # 处理昵称更新请求
                if data.get('type') == 'update_nickname':
                    await handle_nickname_update(websocket, data, game)
                    continue

                # 处理自杀重启请求
                if data.get('type') == 'suicide':
                    response_messages = game.suicide()
                    for msg in response_messages:
                        await websocket.send(json.dumps(msg))
                    continue

                cmd = data.get('cmd')
                response_messages = []

                if cmd == 'move':
                    direction = data.get('dir')
                    response_messages = game.move(direction)

                elif cmd == 'use_item':
                    item_name = data.get('item_name')
                    response_messages = game.use_item(item_name)

                elif cmd == 'merchant_info':
                    response_messages = game.merchant_info()

                elif cmd == 'trade':
                    item_name = data.get('item_name')
                    response_messages = game.trade(item_name)

                elif cmd == 'forge_info':
                    response_messages = game.forge_info()

                elif cmd == 'forge':
                    attribute_index = data.get('attribute_index')
                    if attribute_index is not None:
                        response_messages = game.forge(int(attribute_index))
                    else:
                        response_messages = [{'type': 'log', 'message': '缺少词条索引参数'}]

                else:
                    response_messages = [{
                        'type': 'log',
                        'message': f'未知命令: {cmd}'
                    }]

                # 发送响应消息
                for msg in response_messages:
                    await websocket.send(json.dumps(msg))

            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    'type': 'log',
                    'message': '无效的JSON格式'
                }))
            except Exception as e:
                await websocket.send(json.dumps({
                    'type': 'log',
                    'message': f'服务器错误: {str(e)}'
                }))

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # 清理游戏状态
        if session_id in games:
            del games[session_id]


async def main():
    """启动WebSocket服务器"""
    async with websockets.serve(handle_client, "localhost", 8080):
        await asyncio.Future()  # 永久运行


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
