import asyncio
import json
import websockets
from typing import Dict, List, Optional
from dataclasses import asdict

from map_generator import generate_floor
from game_model import Player, Floor, Position, CellType
from game_logic import (
    move_player, pickup_item, player_attack,
    descend_floor, handle_trade_request, get_merchant_info
)


class GameState:
    """游戏状态管理"""
    def __init__(self):
        self.player: Optional[Player] = None
        self.current_floor: Optional[Floor] = None
        self.floor_level: int = 1
        self.game_over: bool = False
        self.game_over_reason: str = ""
        self.merchant_attempt_count: int = 0  # 商人楼层尝试计数器

    def new_game(self):
        """开始新游戏"""
        self.player = Player()
        self.floor_level = 1
        self.game_over = False
        self.game_over_reason = ""
        self.merchant_attempt_count = 0  # 重置商人楼层尝试计数器

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
            'atk': self.player.atk,
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
            'armor_name': self.player.armor_name
        }

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
            self.game_over = True
            self.game_over_reason = "死亡"
            messages.append({
                'type': 'gameover',
                'reason': self.game_over_reason,
                'final_floor': self.floor_level
            })
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
            self.game_over = True
            self.game_over_reason = "被击败"
            messages.append({
                'type': 'gameover',
                'reason': f"被{monster.name}击败",
                'final_floor': self.floor_level
            })
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
                self.game_over = True
                self.game_over_reason = "死亡"
                messages.append({
                    'type': 'gameover',
                    'reason': self.game_over_reason,
                    'final_floor': self.floor_level
                })

        return messages

    def descend(self) -> List[Dict]:
        """处理进入下一层命令"""
        if self.game_over:
            return [{'type': 'log', 'message': '游戏已结束！'}]

        messages = []

        result = descend_floor(self.player, self.current_floor, self.floor_level)

        if result['logs']:
            messages.append({'type': 'log', 'message': result['logs'][0]})

        if result['success']:
            if self.floor_level >= 100:
                # 通关
                self.game_over = True
                return messages

            # 进入下一层
            self.floor_level += 1
            prev_floor = self.current_floor
            self.current_floor = generate_floor(self.floor_level, prev_floor, self.merchant_attempt_count)
            self.player.position = self.current_floor.player_start_pos

            # 更新商人楼层尝试计数器（使用旧的楼层级别）
            self.update_merchant_attempt_count(self.current_floor, self.floor_level - 1)

            # 发送新楼层地图
            messages.append({
                'type': 'map',
                'grid': self.current_floor.to_serializable_grid(self.player)
            })

            # 更新玩家信息
            messages.append(self.get_player_info_message())

        return messages

    def update_merchant_attempt_count(self, new_floor: Floor, previous_level: int):
        """更新商人楼层尝试计数器"""
        if new_floor.is_merchant_floor:
            # 触发了商人楼层，重置计数器
            if self.merchant_attempt_count > 0:
                print(f"调试：第{previous_level}层触发商人楼层，重置尝试计数器")
            else:
                print(f"调试：第{previous_level}层触发固定的商人楼层")
            self.merchant_attempt_count = 0
        elif previous_level > 10 and previous_level % 10 == 0 and previous_level < 100:
            # 是候选楼层（第20,30,40...）但没有触发，增加计数器
            self.merchant_attempt_count += 1
            print(f"调试：第{previous_level}层未触发商人楼层，尝试次数增加到{self.merchant_attempt_count}")
        elif previous_level == 10:
            print(f"调试：第{previous_level}层固定触发商人楼层，无需重置计数器")

    def merchant_info(self) -> List[Dict]:
        """处理获取商人信息命令"""
        if self.game_over:
            return [{'type': 'log', 'message': '游戏已结束！'}]

        response = get_merchant_info(self.player, self.current_floor)
        return [{'type': 'merchant_info', **response}]

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


# 全局游戏状态存储
# key: session_id, value: GameState
games: Dict[str, GameState] = {}


async def handle_client(websocket):
    """处理WebSocket客户端连接"""
    session_id = str(id(websocket))
    game = GameState()
    games[session_id] = game

    print(f"客户端 {session_id} 已连接")

    try:
        # 发送初始消息
        initial_messages = game.new_game()
        for msg in initial_messages:
            await websocket.send(json.dumps(msg))

        # 处理消息
        async for message in websocket:
            try:
                data = json.loads(message)
                cmd = data.get('cmd')

                response_messages = []

                if cmd == 'move':
                    direction = data.get('dir')
                    response_messages = game.move(direction)

                # 移除手动拾取和下楼命令，改为自动交互
                # elif cmd == 'pickup':
                #     response_messages = game.pickup()

                elif cmd == 'use_item':
                    item_name = data.get('item_name')
                    response_messages = game.use_item(item_name)

                elif cmd == 'merchant_info':
                    response_messages = game.merchant_info()

                elif cmd == 'trade':
                    item_name = data.get('item_name')
                    response_messages = game.trade(item_name)

                # elif cmd == 'descend':
                #     response_messages = game.descend()

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
                print(f"处理消息时出错: {e}")
                await websocket.send(json.dumps({
                    'type': 'log',
                    'message': f'服务器错误: {str(e)}'
                }))

    except websockets.exceptions.ConnectionClosed:
        print(f"客户端 {session_id} 断开连接")
    finally:
        # 清理游戏状态
        if session_id in games:
            del games[session_id]


async def main():
    """启动WebSocket服务器"""
    print("启动爬塔游戏服务器...")
    print("监听地址: ws://localhost:8080")

    async with websockets.serve(handle_client, "localhost", 8080):
        await asyncio.Future()  # 永久运行


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务器已关闭")
