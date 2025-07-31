import asyncio
from typing import List, Dict, Any, Optional
from enum import Enum
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

class GameState(Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    PAUSED = "paused"
    FINISHED = "finished"

class MoveType(Enum):
    JAB = "jab"
    CROSS = "cross"
    HOOK = "hook"
    UPPERCUT = "uppercut"
    BLOCK = "block"
    DODGE = "dodge"
    GUARD = "guard"

@dataclass
class Player:
    id: str
    name: str
    health: int = 100
    score: int = 0
    last_move: Optional[str] = None
    last_move_time: Optional[float] = None
    is_blocking: bool = False
    is_dodging: bool = False

@dataclass
class GameAction:
    player_id: str
    move_type: str
    confidence: float
    timestamp: float

class BoxingGame:
    def __init__(self):
        self.state = GameState.WAITING
        self.players: Dict[str, Player] = {}
        self.round_time = 180  # 3 minutes
        self.current_round = 1
        self.max_rounds = 3
        self.game_start_time: Optional[float] = None
        self.last_update_time: Optional[float] = None
        
        # Move damage values
        self.move_damage = {
            MoveType.JAB: 10,
            MoveType.CROSS: 15,
            MoveType.HOOK: 20,
            MoveType.UPPERCUT: 25,
            MoveType.BLOCK: 0,
            MoveType.DODGE: 0,
            MoveType.GUARD: 0
        }
        
        # Move effectiveness against blocks
        self.move_effectiveness = {
            MoveType.JAB: 0.3,      # 30% damage through block
            MoveType.CROSS: 0.5,    # 50% damage through block
            MoveType.HOOK: 0.7,     # 70% damage through block
            MoveType.UPPERCUT: 0.8, # 80% damage through block
            MoveType.BLOCK: 0.0,
            MoveType.DODGE: 0.0,
            MoveType.GUARD: 0.0
        }

    def add_player(self, player_id: str, name: str) -> Player:
        """Add a new player to the game"""
        player = Player(id=player_id, name=name)
        self.players[player_id] = player
        logger.info(f"Added player: {name} (ID: {player_id})")
        return player

    def remove_player(self, player_id: str) -> bool:
        """Remove a player from the game"""
        if player_id in self.players:
            player_name = self.players[player_id].name
            del self.players[player_id]
            logger.info(f"Removed player: {player_name} (ID: {player_id})")
            return True
        return False

    def start_game(self) -> Dict[str, Any]:
        """Start the boxing game"""
        if len(self.players) < 1:
            raise ValueError("Need at least 1 player to start the game")
        
        self.state = GameState.PLAYING
        self.game_start_time = asyncio.get_event_loop().time()
        self.current_round = 1
        
        # Reset player states
        for player in self.players.values():
            player.health = 100
            player.score = 0
            player.last_move = None
            player.is_blocking = False
            player.is_dodging = False
        
        logger.info("Boxing game started")
        return self.get_state()

    def pause_game(self) -> Dict[str, Any]:
        """Pause the game"""
        self.state = GameState.PAUSED
        logger.info("Game paused")
        return self.get_state()

    def resume_game(self) -> Dict[str, Any]:
        """Resume the game"""
        if self.state == GameState.PAUSED:
            self.state = GameState.PLAYING
            logger.info("Game resumed")
        return self.get_state()

    def end_game(self) -> Dict[str, Any]:
        """End the game"""
        self.state = GameState.FINISHED
        logger.info("Game ended")
        return self.get_state()

    async def process_actions(self, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process incoming actions and update game state"""
        if self.state != GameState.PLAYING:
            return self.get_state()

        current_time = asyncio.get_event_loop().time()
        self.last_update_time = current_time

        # Process each action
        for action_data in actions:
            if 'move' in action_data and 'confidence' in action_data:
                action = GameAction(
                    player_id=action_data.get('player_id', 'player1'),
                    move_type=action_data['move'],
                    confidence=action_data['confidence'],
                    timestamp=action_data.get('timestamp', current_time)
                )
                
                await self._process_single_action(action)

        # Check for round/game end conditions
        await self._check_game_conditions()

        return self.get_state()

    async def _process_single_action(self, action: GameAction):
        """Process a single game action"""
        if action.player_id not in self.players:
            logger.warning(f"Unknown player ID: {action.player_id}")
            return

        player = self.players[action.player_id]
        move_type = MoveType(action.move_type)
        
        # Update player's last move
        player.last_move = action.move_type
        player.last_move_time = action.timestamp
        
        # Handle defensive moves
        if move_type in [MoveType.BLOCK, MoveType.DODGE, MoveType.GUARD]:
            if move_type == MoveType.BLOCK:
                player.is_blocking = True
                player.is_dodging = False
            elif move_type == MoveType.DODGE:
                player.is_dodging = True
                player.is_blocking = False
            elif move_type == MoveType.GUARD:
                player.is_blocking = False
                player.is_dodging = False
            return

        # Handle offensive moves (punches)
        if move_type in [MoveType.JAB, MoveType.CROSS, MoveType.HOOK, MoveType.UPPERCUT]:
            # Find opponent
            opponent = self._get_opponent(action.player_id)
            if opponent:
                damage = self._calculate_damage(move_type, action.confidence, opponent)
                self._apply_damage(opponent, damage, move_type)
                
                # Award points for successful hits
                if damage > 0:
                    player.score += damage
                    logger.info(f"{player.name} landed {move_type.value} for {damage} damage!")

    def _get_opponent(self, player_id: str) -> Optional[Player]:
        """Get the opponent of a player"""
        if len(self.players) == 1:
            # Single player mode - opponent is AI
            return None
        
        opponent_id = None
        for pid in self.players.keys():
            if pid != player_id:
                opponent_id = pid
                break
        
        return self.players.get(opponent_id) if opponent_id else None

    def _calculate_damage(self, move_type: MoveType, confidence: float, opponent: Player) -> int:
        """Calculate damage for a move"""
        base_damage = self.move_damage[move_type]
        
        # Apply confidence multiplier
        damage = int(base_damage * confidence)
        
        # Check if opponent is blocking
        if opponent.is_blocking:
            effectiveness = self.move_effectiveness[move_type]
            damage = int(damage * effectiveness)
        
        # Check if opponent is dodging
        if opponent.is_dodging:
            damage = 0  # Dodging completely avoids damage
        
        return max(0, damage)

    def _apply_damage(self, player: Player, damage: int, move_type: MoveType):
        """Apply damage to a player"""
        old_health = player.health
        player.health = max(0, player.health - damage)
        
        logger.info(f"{player.name} took {damage} damage from {move_type.value} "
                   f"(Health: {old_health} -> {player.health})")

    async def _check_game_conditions(self):
        """Check for round/game end conditions"""
        # Check if any player is knocked out
        for player in self.players.values():
            if player.health <= 0:
                await self._handle_knockout(player)
                return

        # Check round time limit
        if self.game_start_time:
            elapsed_time = asyncio.get_event_loop().time() - self.game_start_time
            if elapsed_time >= self.round_time:
                await self._handle_round_end()

    async def _handle_knockout(self, knocked_out_player: Player):
        """Handle a player being knocked out"""
        logger.info(f"{knocked_out_player.name} has been knocked out!")
        
        # Find the winner
        winner = None
        for player in self.players.values():
            if player.id != knocked_out_player.id:
                winner = player
                break
        
        if winner:
            winner.score += 50  # Bonus points for knockout
            logger.info(f"{winner.name} wins by knockout!")
        
        self.state = GameState.FINISHED

    async def _handle_round_end(self):
        """Handle round end"""
        logger.info("Round ended - calculating scores...")
        
        # Determine round winner based on health and score
        players_list = list(self.players.values())
        if len(players_list) >= 2:
            # Sort by health first, then by score
            players_list.sort(key=lambda p: (p.health, p.score), reverse=True)
            winner = players_list[0]
            winner.score += 25  # Round win bonus
            
            logger.info(f"{winner.name} wins the round!")
        
        self.current_round += 1
        
        if self.current_round > self.max_rounds:
            self.state = GameState.FINISHED
            logger.info("Game finished - all rounds completed")
        else:
            # Start next round
            self.game_start_time = asyncio.get_event_loop().time()
            for player in self.players.values():
                player.health = 100  # Reset health for new round
                player.is_blocking = False
                player.is_dodging = False

    def get_state(self) -> Dict[str, Any]:
        """Get current game state"""
        return {
            "state": self.state.value,
            "current_round": self.current_round,
            "max_rounds": self.max_rounds,
            "round_time": self.round_time,
            "players": [self._player_to_dict(p) for p in self.players.values()],
            "game_start_time": self.game_start_time,
            "last_update_time": self.last_update_time
        }

    def get_players(self) -> List[Dict[str, Any]]:
        """Get list of players"""
        return [self._player_to_dict(p) for p in self.players.values()]

    def get_score(self) -> Dict[str, int]:
        """Get current scores"""
        return {p.id: p.score for p in self.players.values()}

    def _player_to_dict(self, player: Player) -> Dict[str, Any]:
        """Convert player to dictionary"""
        return {
            "id": player.id,
            "name": player.name,
            "health": player.health,
            "score": player.score,
            "last_move": player.last_move,
            "last_move_time": player.last_move_time,
            "is_blocking": player.is_blocking,
            "is_dodging": player.is_dodging
        }

    def reset(self):
        """Reset the game to initial state"""
        self.state = GameState.WAITING
        self.players.clear()
        self.current_round = 1
        self.game_start_time = None
        self.last_update_time = None
        logger.info("Game reset") 