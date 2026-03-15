from __future__ import annotations
"""
SQLAlchemy models — schema is designed to support all 4 phases without
structural changes. Phase 3/4 columns default to null/zero until activated.
"""
from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Integer,
    String, ForeignKey, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship
import uuid


class Base(DeclarativeBase):
    pass


class Server(Base):
    """One row per Discord guild."""
    __tablename__ = "servers"

    guild_id      = Column(BigInteger, primary_key=True)
    tier          = Column(String(20), nullable=False, default="free")  # 'free' | 'premium'
    games_today   = Column(Integer, nullable=False, default=0)
    games_date    = Column(DateTime, nullable=True)   # date of last games_today reset
    created_at    = Column(DateTime, nullable=False, default=func.now())
    premium_since = Column(DateTime, nullable=True)   # Phase 4
    premium_until = Column(DateTime, nullable=True)   # Phase 4


class User(Base):
    """One row per (user, guild) pair — stats are server-scoped."""
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, autoincrement=True)
    user_id         = Column(BigInteger, nullable=False)
    guild_id        = Column(BigInteger, nullable=False)
    display_name    = Column(String(100), nullable=True)   # cached for display when member leaves
    games_played    = Column(Integer, nullable=False, default=0)
    games_won       = Column(Integer, nullable=False, default=0)
    rounds_played   = Column(Integer, nullable=False, default=0)
    correct_guesses = Column(Integer, nullable=False, default=0)
    # Daily game tracking — mirrors servers.games_today pattern
    games_today     = Column(Integer,  nullable=False, default=0)
    games_date      = Column(DateTime, nullable=True)   # date of last games_today reset
    # Phase 3: murderer-among-players mode stats
    murderer_games  = Column(Integer, nullable=False, default=0)
    murderer_wins   = Column(Integer, nullable=False, default=0)
    created_at      = Column(DateTime, nullable=False, default=func.now())


class Game(Base):
    """Completed game record — written at game end."""
    __tablename__ = "games"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    guild_id     = Column(BigInteger, nullable=False)
    channel_id   = Column(BigInteger, nullable=False)
    genre        = Column(String(50),  nullable=True)
    era          = Column(String(50),  nullable=True)
    setting      = Column(String(100), nullable=True)
    # 'standard' | 'murderer_among_players' (Phase 3)
    mode         = Column(String(30), nullable=False, default="standard")
    player_count = Column(Integer,    nullable=True)
    rounds_played= Column(Integer,    nullable=True)
    # 'solved' | 'unsolved' | 'murderer_eliminated' | 'abandoned'
    outcome           = Column(String(30), nullable=True)
    # Beta telemetry
    correct_guess_count  = Column(Integer, nullable=True)   # how many players guessed right
    murderer_elim_round  = Column(Integer, nullable=True)   # round murderer was eliminated, null otherwise
    started_at   = Column(DateTime,   nullable=False, default=func.now())
    ended_at     = Column(DateTime,   nullable=True)

    players  = relationship("GamePlayer",  back_populates="game", cascade="all, delete-orphan")
    feedback = relationship("GameFeedback", back_populates="game", cascade="all, delete-orphan")


class GamePlayer(Base):
    """One row per player per game."""
    __tablename__ = "game_players"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    game_id           = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    user_id           = Column(BigInteger, nullable=False)
    # 'detective' | 'murderer' (Phase 3)
    role              = Column(String(20), nullable=False, default="detective")
    guessed_correctly = Column(Boolean,    nullable=True)
    final_guess       = Column(String(100),nullable=True)
    votes_cast        = Column(Integer,    nullable=False, default=0)   # rounds player voted in
    joined_at         = Column(DateTime,   nullable=False, default=func.now())

    game = relationship("Game", back_populates="players")


class GameFeedback(Base):
    """
    Per-player, per-game feedback collected via ephemeral post-game buttons.
    Two signals captured: did the Plottwyst fool them, and overall case rating.
    """
    __tablename__ = "game_feedback"

    id               = Column(Integer,          primary_key=True, autoincrement=True)
    game_id          = Column(UUID(as_uuid=True), ForeignKey("games.id"), nullable=False)
    user_id          = Column(BigInteger,        nullable=False)
    guild_id         = Column(BigInteger,        nullable=False)
    # 'yes' | 'almost' | 'no'
    plottwyst_fooled = Column(String(20),        nullable=True)
    # 'loved' | 'good' | 'okay' | 'confused'
    case_rating      = Column(String(20),        nullable=True)
    created_at       = Column(DateTime,          nullable=False, default=func.now())

    game = relationship("Game", back_populates="feedback")


class LimitHit(Base):
    """
    Logged every time a free-tier server hits a usage limit.
    Used to identify upsell candidates.
    """
    __tablename__ = "limit_hits"

    id         = Column(Integer,    primary_key=True, autoincrement=True)
    guild_id   = Column(BigInteger, nullable=False)
    user_id    = Column(BigInteger, nullable=False)   # user who tried to start
    channel_id = Column(BigInteger, nullable=False)   # channel where it happened
    # 'daily_game_limit' | 'max_players' (extensible for future limits)
    limit_type = Column(String(30), nullable=False, default="daily_game_limit")
    hit_at     = Column(DateTime,   nullable=False, default=func.now())


class Subscription(Base):
    """Phase 4: payment/subscription tracking."""
    __tablename__ = "subscriptions"

    id            = Column(Integer,     primary_key=True, autoincrement=True)
    guild_id      = Column(BigInteger,  nullable=False)
    plan          = Column(String(20),  nullable=False)
    started_at    = Column(DateTime,    nullable=False, default=func.now())
    expires_at    = Column(DateTime,    nullable=True)
    payment_ref   = Column(String(200), nullable=True)
