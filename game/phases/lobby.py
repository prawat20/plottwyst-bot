from __future__ import annotations
"""Lobby phase helpers — state mutations only, no Discord UI (that lives in views)."""
from game.state import GameState, PlayerState
from game import session_manager


async def add_player(state: GameState, user_id: int, display_name: str) -> bool:
    """Add a player to the lobby. Returns False if already joined."""
    if user_id in state.players:
        return False
    state.players[user_id] = PlayerState(user_id=user_id, display_name=display_name)
    await session_manager.save(state)
    return True


async def remove_player(state: GameState, user_id: int) -> bool:
    """Remove a player from the lobby. Returns False if not in lobby."""
    if user_id not in state.players:
        return False
    del state.players[user_id]
    await session_manager.save(state)
    return True


def can_start(state: GameState, user_id: int, max_players: int) -> tuple[bool, str]:
    """Returns (can_start, reason). reason is empty when allowed."""
    if user_id != state.creator_id:
        return False, "Only the game creator can start the game."
    if len(state.players) < 1:
        return False, "You need at least **1 player** to start."
    if len(state.players) > max_players:
        return False, f"Too many players (max {max_players} for your tier)."
    return True, ""
