# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Tower Climbing Game - a turn-based roguelike where players climb from floor 1 to 100 and defeat the final boss. The game uses Python backend with WebSocket communication and HTML5 Canvas frontend.

## Architecture

The project follows clean MVC architecture with clear separation of concerns:

**Backend Core Files:**
- `game_model.py` - Data models (Player, Monster, Floor, Item, Position classes)
- `game_logic.py` - Game mechanics (combat, movement, interaction systems)
- `map_generator.py` - Procedural level generation with strategic enemy placement
- `game_server.py` - WebSocket server and game state management
- `save_load.py` - Save/load system with JSON persistence

**Frontend:**
- `index.html` - Complete HTML5 Canvas game interface with WebSocket client

## Development Commands

### Setup
```bash
# Install the only required dependency
pip install websockets
```

### Running the Game
```bash
# Start the backend server (runs on ws://localhost:8080)
python game_server.py

# Open frontend in browser - simply open index.html in any modern browser
```

### Testing
```bash
# Compile check for syntax errors
python -m py_compile game_model.py game_logic.py map_generator.py game_server.py save_load.py
```

## Key Technical Details

### WebSocket Communication Protocol
**Client Commands:**
```json
{"cmd": "move", "dir": "up"}
{"cmd": "use_item", "item_name": "小血瓶"}
```

**Server Responses:**
```json
{"type": "map", "grid": [...]}
{"type": "info", "hp": 500, "atk": 50, ...}
{"type": "log", "message": "You moved!"}
{"type": "auto_pickup", "item": {...}}
{"type": "gameover", "reason": "Victory!"}
```

### Game Systems Architecture
- **Turn-Based Combat**: Player always attacks first, damage formula `max(1, attack - defense)`
- **Guard Focus System**: Strategic enemy placement around items using Manhattan distance
- **Flood Fill Algorithm**: Detects connected room areas
- **Auto-Interaction**: Movement triggers item pickup and floor descent
- **Room Restriction**: Cannot access items/stairs while monsters exist in current room

### Map Generation
- Room + corridor layout (4-6 rooms per floor)
- 15×15 grid-based movement
- Exponential monster stat scaling with floor level
- Weight-based priority: Weapons/Armor (40%) > Stairs (30%) > Potions (20%)

## Important Development Notes

- Only external dependency is `websockets` library
- Uses pure Python standard library (asyncio, json, typing, dataclasses, enum, random, os)
- Save/load system implemented but not integrated into WebSocket commands
- All file operations should use absolute Windows paths due to potential path bugs
- Game state is managed server-side, client only renders and sends commands