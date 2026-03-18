from __future__ import annotations
"""
Settings panel — ephemeral View shown to the host in the lobby.

Free settings (all hosts): Discussion Speed, Voting Time, Guess Time, Voting Mode.
Locked settings (shown, not interactive): Difficulty, Custom Story.
"""
import discord
from game import session_manager

# ── Option definitions ────────────────────────────────────────────────────────

_SPEED_OPTIONS = [
    discord.SelectOption(label="🐢  Slow",    value="slow",   description="Discussion: 4 min R1  ·  3 min R2+"),
    discord.SelectOption(label="⚖️  Normal",  value="normal", description="Discussion: 3 min R1  ·  2 min R2+  (default)", default=True),
    discord.SelectOption(label="⚡  Fast",    value="fast",   description="Discussion: 90s R1  ·  60s R2+"),
]

_VOTE_TIME_OPTIONS = [
    discord.SelectOption(label="30 seconds", value="30", description="Default", default=True),
    discord.SelectOption(label="60 seconds", value="60"),
    discord.SelectOption(label="90 seconds", value="90"),
]

_GUESS_TIME_OPTIONS = [
    discord.SelectOption(label="30 seconds", value="30"),
    discord.SelectOption(label="45 seconds", value="45", description="Default", default=True),
    discord.SelectOption(label="60 seconds", value="60"),
]

_MODE_OPTIONS = [
    discord.SelectOption(
        label="🗡️  Classic",
        value="classic",
        description="Vote out murderer = game ends immediately",
        default=True,
    ),
    discord.SelectOption(
        label="🔍  Silent Investigation",
        value="silent",
        description="Game always runs to final guess — no mid-game reveal",
    ),
]


def _times_from_speed(speed: str) -> tuple[int, int]:
    return {"slow": (240, 180), "normal": (180, 120), "fast": (90, 60)}[speed]


def _speed_from_times(r1: int, r2: int) -> str:
    if r1 <= 90:  return "fast"
    if r1 >= 240: return "slow"
    return "normal"


def _mark_default(options: list[discord.SelectOption], value: str) -> list[discord.SelectOption]:
    for opt in options:
        opt.default = (opt.value == value)
    return options


# ── Settings embed ────────────────────────────────────────────────────────────

def _build_settings_embed() -> discord.Embed:
    embed = discord.Embed(
        title="⚙️  Game Settings",
        description=(
            "Adjust settings below — changes apply when you click **Apply**.\n\n"
            "🔒 **Premium settings** are shown below but require an upgrade to unlock."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="🔒  Difficulty",
        value="Easy / Medium / Hard  ·  *Upgrade to Premium to unlock*",
        inline=False,
    )
    embed.add_field(
        name="🔒  Custom Story",
        value="Seed your own victim and setting  ·  *Upgrade to Premium to unlock*",
        inline=False,
    )
    embed.set_footer(text="Free settings apply to all hosts  ·  /premium info for upgrades")
    return embed


# ── Settings View ─────────────────────────────────────────────────────────────

class SettingsView(discord.ui.View):
    """
    Ephemeral settings panel. Receives the LobbyView so it can refresh the
    lobby embed and pass the selected genre key back correctly.
    """

    def __init__(self, lobby_view: "LobbyView"):  # type: ignore[name-defined]
        super().__init__(timeout=120)
        self.lobby_view = lobby_view
        state = lobby_view.state

        # Resolve current values for default selection
        current_speed = _speed_from_times(state.discussion_time_r1, state.discussion_time_r2)
        current_vote  = str(state.voting_time)
        current_guess = str(state.guess_time)
        current_mode  = state.voting_mode

        self.add_item(discord.ui.Select(
            placeholder="⏱️  Discussion Speed",
            options=_mark_default(list(_SPEED_OPTIONS), current_speed),
            custom_id="speed",
            row=0,
        ))
        self.add_item(discord.ui.Select(
            placeholder="🗳️  Voting Time",
            options=_mark_default(list(_VOTE_TIME_OPTIONS), current_vote),
            custom_id="vote_time",
            row=1,
        ))
        self.add_item(discord.ui.Select(
            placeholder="🎯  Final Guess Time",
            options=_mark_default(list(_GUESS_TIME_OPTIONS), current_guess),
            custom_id="guess_time",
            row=2,
        ))
        self.add_item(discord.ui.Select(
            placeholder="🗡️  Voting Mode",
            options=_mark_default(list(_MODE_OPTIONS), current_mode),
            custom_id="voting_mode",
            row=3,
        ))

    def _get_select_value(self, custom_id: str) -> str | None:
        for item in self.children:
            if isinstance(item, discord.ui.Select) and item.custom_id == custom_id:
                return item.values[0] if item.values else None
        return None

    @discord.ui.button(label="Apply Settings", style=discord.ButtonStyle.success, emoji="✅", row=4)
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        from bot.views.lobby_view import build_lobby_embed

        speed      = self._get_select_value("speed")      or "normal"
        vote_time  = self._get_select_value("vote_time")  or "30"
        guess_time = self._get_select_value("guess_time") or "45"
        mode       = self._get_select_value("voting_mode") or "classic"

        r1, r2 = _times_from_speed(speed)

        # Load state, apply, save
        state = await session_manager.load(self.lobby_view.state.channel_id)
        if state is None:
            await interaction.response.send_message("Lobby no longer exists.", ephemeral=True)
            return

        state.discussion_time_r1 = r1
        state.discussion_time_r2 = r2
        state.voting_time        = int(vote_time)
        state.guess_time         = int(guess_time)
        state.voting_mode        = mode
        await session_manager.save(state)

        # Keep lobby_view in sync so Start picks up current state
        self.lobby_view.state = state

        # Refresh lobby embed to show settings summary
        if self.lobby_view.lobby_msg:
            try:
                await self.lobby_view.lobby_msg.edit(
                    embed=build_lobby_embed(
                        state,
                        self.lobby_view.max_players,
                        self.lobby_view.selected_genre_key,
                    ),
                    view=self.lobby_view,
                )
            except Exception:
                pass

        await interaction.response.send_message(
            "✅ Settings applied!", ephemeral=True
        )
        self.stop()
