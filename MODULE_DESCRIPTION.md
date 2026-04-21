# Board Game Concept - Module Description

## Overview

The **Board Game Concept** is a turn-based, multiplayer strategy game framework where players create custom unit types, deploy them on a shared board, and program their actions to compete autonomously. The project implements a client-server architecture that manages game state, validates moves, processes turns, and determines winners through automated game resolution.

## Core Purpose

This module demonstrates:
- **Custom Unit Creation**: Players define their own unit types with configurable stats (attack, health, energy, movement speed)
- **Distributed Gameplay**: Multiple players interact through a centralized server that coordinates commits and turn resolution
- **Autonomous Gameplay**: Once units are deployed and programmed, they execute their strategies automatically
- **Game Observation**: Real-time observation of game state from a neutral perspective

## Architecture Components

### 1. **BoardGameConcept.py** - Core Game Engine
Defines the fundamental game objects and rules:

- **Empty**: Represents unoccupied board spaces
- **Player**: Player abstraction with unique player number identification
- **UnitType**: Defines unit specifications including:
  - Name and symbol (single character representation)
  - Attack power (1-10 damage per attack)
  - Health (total hit points)
  - Energy (movement/action resource)
  - Speed (frequency of movement: 1-10, where 10 = once per tick, 1 = once every 10 ticks)
  - Direction constants (NORTH, EAST, SOUTH, WEST)
  - State constants (INITIAL, MOVING, NOP for no-operation)
- **Board**: Game board grid management with size configuration (customizable X and Y dimensions)

### 2. **GameData.py** - Game State Manager
Manages all persistent game data and provides data access methods:

- Maintains player information and unit definitions
- Tracks board state and board visibility (what each player can see)
- Stores unprocessed moves pending commit
- Provides getter/setter methods for game state components
- Handles data persistence to disk (YAML format)
- Manages player-specific board views based on unit positions and visibility

### 3. **server.py** - Game Coordinator & Administrator
The server runs continuously as player 0 (game administrator) and performs:

- **Game Initialization**: Loads board configuration and player data from files
- **State Management**: Loads and maintains current game state from disk
- **Turn Processing**: Waits for all players to commit their moves, then applies them simultaneously
- **Synchronization**: Acts as the commit authority—applies actions only when all players have committed
- **Game Resolution**: Determines game state after each turn (active units, winners, losers)

Command support includes:
- `add player` - Register new players to the game
- `load board` - Import board configuration from files
- `load player` - Import player definitions and units
- `set board` - Define board dimensions (before game start)
- `show board` - Display current board state
- `show player` - Display player information
- `show types` - Display defined unit types
- `commit` - Process all pending moves

### 4. **client.py** - Player Interface
Provides interactive command-line interface for players (non-administrator):

- **Unit Management**: Create and manage custom unit types
- **Unit Deployment**: Place units on the board at specific coordinates
- **Unit Commands**: Issue move commands (north, south, east, west) to units
- **Information Display**: View player stats, unit types, units, and board state
- **Commit Protocol**: Send final set of moves to server for processing

Command support includes:
- `add type` - Define new unit types with stats
- `add unit` - Deploy a unit on the board
- `show player` - View player information
- `show types` - View all known unit types (own and observed enemy types)
- `show units` - View all known units (own and observed enemy units)
- `show board` - Display board from player's perspective
- `move` - Issue movement commands to units
- `commit` - Commit turn actions to server

### 5. **observer.py** - Neutral Game Observer
Provides read-only observation of game state:

- Monitors all game activity without player affiliation
- Displays complete game state information
- Tracks pending moves before commit
- Updates dynamically as the game progresses

Command support includes:
- `reload` - Refresh game data from disk
- `show players` - Display all player information
- `show types` - Display all unit types
- `show units` - Display all units on board
- `show pending` - Display actions queued for next commit
- `show board` - Display full board state

## Game Flow

1. **Initialization Phase**:
   - Server (player 0) loads board configuration and player data files
   - Players are registered with their unit type definitions
   - Board dimensions are set

2. **Unit Definition Phase**:
   - Each player defines custom unit types using the client
   - Units are created with specific attack, health, and energy values

3. **Deployment Phase**:
   - Players deploy units on the board at specific coordinates
   - Each player issues movement and action commands to their units

4. **Commit Phase**:
   - Players issue `commit` command to finalize their turn
   - Server waits for all players to commit
   - Once all commits received, server applies moves simultaneously

5. **Resolution Phase**:
   - Game rules are applied (movement, attacks, damage)
   - Units with health ≤ 0 are eliminated
   - Board state is updated for next turn

6. **Win Condition**:
   - Game continues until only one player has functional units remaining
   - Last player with a surviving unit wins

## Data Persistence

- **YAML Format**: Game configuration and state stored in YAML files
- **File-Based Storage**: Player configurations, board definitions, and game state use disk files
- **Directory Structure**: Game data organized by game number for multi-game support

## Dependencies

- **Python 3.x**: Core language
- **PyYAML**: YAML file parsing and generation
- **board**: Board game library for game mechanics
- **expect**: Used in test suite for interactive testing automation
- **dos2unix**: Line-ending conversion for cross-platform compatibility

## Testing Framework

- **Test Suite**: Automated tests using expect scripts for interactive command sequences
- **Test Scenarios**:
  - Server interactive startup
  - Server interactive game load
  - Player interactive setup
  - Server automated load
- **Test Data**: Sample board and player configuration files (board.yaml, player_1.yaml, player_2.yaml)

## Key Design Patterns

1. **Client-Server Architecture**: Distributed game coordination through centralized server
2. **Observer Pattern**: Neutral observer monitors game state without player bias
3. **State Machine**: Game progresses through defined phases (initialization → deployment → resolution)
4. **Synchronization Protocol**: Atomic commits ensure simultaneous move processing
5. **Visibility Model**: Players have limited board views based on their unit positions

## Future Enhancements

1. **Web Service Integration**: Flask-based REST API to expose CLI commands
2. **Database Persistence**: Migration from file-based to SQLite storage
3. **Game Initialization Script**: Dedicated setup utility (`initgame.py`)
4. **Data Model Refactoring**: Separation of database concerns from GameData class

## Use Cases

- **Game Strategy Development**: Test and refine unit strategies
- **AI Agent Training**: Program units with different AI strategies and observe competition
- **Educational Platform**: Learn game design, distributed systems, and turn-based mechanics
- **Multiplayer Gaming**: Support for multiple concurrent players over network (with web service)

## Summary

The Board Game Concept is a flexible, extensible framework for creating and hosting turn-based strategic games. It abstracts the complexity of multiplayer game coordination while providing a simple interface for players to define custom units and issue commands. The modular design allows for future enhancements while maintaining the core gameplay loop of simultaneous-move commitment and atomic turn resolution.
