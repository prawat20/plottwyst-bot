from __future__ import annotations
"""
Settings panel — button-based, ephemeral, host-only.

Layout (5 rows):
  Row 0  ⏱️ Discussion Speed  — [🐢 Slow] [⚖️ Normal] [⚡ Fast]
  Row 1  🗳️ Voting Time       — [30s] [60s] [90s]
  Row 2  🎯 Final Guess Time  — [30s] [45s] [60s]
  Row 3  🗡️ Voting Mode       — [🗡️ Classic] [🔍 Silent Investigation]
  Row 4  Premium + Done       — [🔒 Difficulty] [🔒 Custom Story] [✅ Done]

Active selection = ButtonStyle.primary (blue).
Inactive options = ButtonStyle.secondary (grey).
Premium buttons  = disabled grey.

The embed updates live on every button click so the host always sees the
current value for each setting without having to map rows mentally.
Changes are persisted to Redis only when Done is clicked.
"""
import discord
from game import session_manager


# ── Helpers ───────────────────────────────────────────────────────────────────

def _times_from_speed(speed: str) -> tuple[int, int]:
    return {"slow": (240, 180), "normal": (180, 120), "fast": (90, 60)}[speed]


def _speed_from_times(r1: int, r2: int) -> str:
    if r1 <= 90:  return "fast"
    if r1 >= 240: return "slow"
    return "normal"


_SPEED_LABEL = {"slow": "🐢  Slow", "normal": "⚖️  Normal", "fast": "⚡  Fast"}
_MODE_LABEL  = {"classic": "🗡️  Classic", "silent": "🔍  Silent Investigation"}


# ── Live embed ────────────────────────────────────────────────────────────────

def _build_embed(speed: str, vote: str, guess: str, mode: str) -> discord.Embed:
    embed = discord.Embed(
        title="⚙️  Game Settings",
        description="Select an option in each row. Hit **✅ Done** to save.",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="⏱️  Discussion Speed",  value=_SPEED_LABEL.get(speed, speed),  inline=True)
    embed.add_field(name="🗳️  Voting Time",        value=f"{vote}s",                       inline=True)
    embed.add_field(name="🎯  Final Guess Time",   value=f"{guess}s",                      inline=True)
    embed.add_field(name="🗡️  Voting Mode",        value=_MODE_LABEL.get(mode, mode),      inline=False)
    embed.add_field(
        name="🔒  Premium (locked)",
        value="**Difficulty** · **Custom Story**  —  `/premium info` to unlock",
        inline=False,
    )
    return embed


# ── Option button ─────────────────────────────────────────────────────────────

class _OptionBtn(discord.ui.Button):
    """One selectable option within a setting group."""

    def __init__(self, label: str, value: str, group: str, active: bool, row: int):
        super().__init__(
            label=label,
            style=discord.ButtonStyle.primary if active else discord.ButtonStyle.secondary,
            row=row,
        )
        self.value = value
        self.group = group  # "speed" | "vote_time" | "guess_time" | "mode"

    async def callback(self, interaction: discord.Interaction):
        view: SettingsView = self.view  # type: ignore[assignment]
        # Update the tracked value for this group
        setattr(view, f"_{self.group}", self.value)
        view._sync_styles()
        await interaction.response.edit_message(embed=view.current_embed(), view=view)


# ── Settings View ─────────────────────────────────────────────────────────────

class SettingsView(discord.ui.View):
    """Ephemeral button-based settings panel. Pass lobby_view on construction."""

    def __init__(self, lobby_view: "LobbyView"):  # type: ignore[name-defined]
        super().__init__(timeout=120)
        self.lobby_view = lobby_view
        state = lobby_view.state

        # Current values — mutated by button clicks before Done saves them
        self._speed      = _speed_from_times(state.discussion_time_r1, state.discussion_time_r2)
        self._vote_time  = str(state.voting_time)
        self._guess_time = str(state.guess_time)
        self._mode       = state.voting_mode

        self._build_buttons()

    # ── Button construction ───────────────────────────────────────────────────

    def _build_buttons(self) -> None:
        # Row 0 — Discussion Speed
        for label, value in [("🐢  Slow", "slow"), ("⚖️  Normal", "normal"), ("⚡  Fast", "fast")]:
            self.add_item(_OptionBtn(label, value, "speed", value == self._speed, row=0))

        # Row 1 — Voting Time
        for label, value in [("Vote: 30s", "30"), ("Vote: 60s", "60"), ("Vote: 90s", "90")]:
            self.add_item(_OptionBtn(label, value, "vote_time", value == self._vote_time, row=1))

        # Row 2 — Final Guess Time
        for label, value in [("Guess: 30s", "30"), ("Guess: 45s", "45"), ("Guess: 60s", "60")]:
            self.add_item(_OptionBtn(label, value, "guess_time", value == self._guess_time, row=2))

        # Row 3 — Voting Mode
        for label, value in [("🗡️  Classic", "classic"), ("🔍  Silent Investigation", "silent")]:
            self.add_item(_OptionBtn(label, value, "mode", value == self._mode, row=3))

        # Row 4 — Premium (locked) + Done
        self.add_item(discord.ui.Button(
            label="🔒  Difficulty",
            style=discord.ButtonStyle.secondary,
            disabled=True,
            row=4,
        ))
        self.add_item(discord.ui.Button(
            label="🔒  Custom Story",
            style=discord.ButtonStyle.secondary,
            disabled=True,
            row=4,
        ))
        done_btn = discord.ui.Button(
            label="✅  Done",
            style=discord.ButtonStyle.success,
            row=4,
        )
        done_btn.callback = self._on_done
        self.add_item(done_btn)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _sync_styles(self) -> None:
        """Re-colour buttons after a selection change."""
        current = {
            "speed":      self._speed,
            "vote_time":  self._vote_time,
            "guess_time": self._guess_time,
            "mode":       self._mode,
        }
        for item in self.children:
            if isinstance(item, _OptionBtn):
                item.style = (
                    discord.ButtonStyle.primary
                    if item.value == current[item.group]
                    else discord.ButtonStyle.secondary
                )

    def current_embed(self) -> discord.Embed:
        return _build_embed(self._speed, self._vote_time, self._guess_time, self._mode)

    # ── Done callback ─────────────────────────────────────────────────────────

    async def _on_done(self, interaction: discord.Interaction) -> None:
        from bot.views.lobby_view import build_lobby_embed

        r1, r2 = _times_from_speed(self._speed)

        state = await session_manager.load(self.lobby_view.state.channel_id)
        if state is None:
            await interaction.response.edit_message(
                embed=discord.Embed(description="Lobby no longer exists.", color=discord.Color.red()),
                view=None,
            )
            return

        state.discussion_time_r1 = r1
        state.discussion_time_r2 = r2
        state.voting_time        = int(self._vote_time)
        state.guess_time         = int(self._guess_time)
        state.voting_mode        = self._mode
        await session_manager.save(state)

        # Keep lobby_view in sync so Start picks up the new values
        self.lobby_view.state = state

        # Refresh the lobby embed so everyone sees the updated settings summary
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

        await interaction.response.edit_message(
            embed=discord.Embed(
                description="✅  Settings saved!",
                color=discord.Color.green(),
            ),
            view=None,
        )
        self.stop()
