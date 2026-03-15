from __future__ import annotations
"""Lobby UI — Join Game, Start Game, and Genre Select."""
import discord
from game.state import GameState
from game import session_manager
from game.phases.lobby import add_player, can_start
from engine.prompts.genres import GENRE_MENU, genre_display_name
from db.session import AsyncSessionLocal
from db.repositories import limit_hit_repo


def build_lobby_embed(
    state: GameState,
    max_players: int,
    genre_key: str = "random",
) -> discord.Embed:
    player_count = len(state.players)
    player_lines = "\n".join(
        f"🔹 {p.display_name}" for p in state.players.values()
    ) or "*No detectives yet — be the first to join!*"

    embed = discord.Embed(
        title="🔍  PLOTTWYST — Murder Mystery Lobby",
        description=(
            "A crime has been committed. Gather your team, study the suspects, "
            "and name the murderer before the trail goes cold.\n\n"
            "**Join the lobby below.** The host can start once everyone is in."
        ),
        color=discord.Color.dark_blue(),
    )
    embed.add_field(
        name=f"Detectives  ({player_count}/{max_players})",
        value=player_lines,
        inline=False,
    )
    embed.add_field(
        name="Story Setting",
        value=genre_display_name(genre_key),
        inline=True,
    )
    embed.add_field(
        name="How to Play",
        value="New to Plottwyst? Use `/howtoplay`",
        inline=True,
    )
    slots_left  = max_players - player_count
    slots_text  = f"{slots_left} slot{'s' if slots_left != 1 else ''} remaining" if slots_left > 0 else "Lobby full"
    embed.set_footer(text=f"{slots_text}  ·  Lobby expires in 5 minutes")
    return embed


class GenreSelect(discord.ui.Select):
    def __init__(self, is_premium: bool):
        options = []
        for entry in GENRE_MENU:
            locked = entry["premium"] and not is_premium
            label  = f"{entry['label']}  🔒" if locked else entry["label"]
            desc   = "Upgrade to Premium to unlock" if locked else entry["description"]
            options.append(discord.SelectOption(
                label=label,
                value=entry["key"],
                emoji=entry["emoji"],
                description=desc,
                default=(entry["key"] == "random"),
            ))
        super().__init__(
            placeholder="🎭  Choose a story setting…",
            min_values=1,
            max_values=1,
            options=options,
            row=1,
        )
        self.is_premium = is_premium

    async def callback(self, interaction: discord.Interaction):
        view: LobbyView = self.view  # type: ignore[assignment]

        # Only the creator can change the setting
        if interaction.user.id != view.state.creator_id:
            await interaction.response.send_message(
                "Only the host can change the story setting.", ephemeral=True
            )
            return

        chosen_key = self.values[0]
        entry      = next(g for g in GENRE_MENU if g["key"] == chosen_key)

        # Block free users from premium genres
        if entry["premium"] and not self.is_premium:
            async with AsyncSessionLocal() as session:
                await limit_hit_repo.record(
                    session    = session,
                    guild_id   = interaction.guild_id,
                    user_id    = interaction.user.id,
                    channel_id = interaction.channel_id,
                    limit_type = "premium_genre",
                )
            # Reset the select back to random visually
            for opt in self.options:
                opt.default = (opt.value == "random")
            await interaction.response.edit_message(
                embed=build_lobby_embed(view.state, view.max_players, view.selected_genre_key),
                view=view,
            )
            await interaction.followup.send(
                f"**{entry['emoji']}  {entry['label']}** is a Premium setting.\n"
                "Use `/premium info` to see what's included in Premium.",
                ephemeral=True,
            )
            return

        # Apply selection
        view.selected_genre_key = chosen_key
        for opt in self.options:
            opt.default = (opt.value == chosen_key)

        await interaction.response.edit_message(
            embed=build_lobby_embed(view.state, view.max_players, chosen_key),
            view=view,
        )


class LobbyView(discord.ui.View):
    def __init__(self, state: GameState, max_players: int, is_premium: bool = False):
        super().__init__(timeout=300)  # lobby expires after 5 minutes
        self.state              = state
        self.max_players        = max_players
        self.is_premium         = is_premium
        self.lobby_msg: discord.Message | None = None
        self.started: bool      = False
        self.selected_genre_key = "random"

        self.add_item(GenreSelect(is_premium=is_premium))

    @discord.ui.button(label="Join Game", style=discord.ButtonStyle.success, emoji="🕵️", row=2)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = await session_manager.load(self.state.channel_id)
        if state is None:
            await interaction.response.send_message("This lobby no longer exists.", ephemeral=True)
            return
        if state.phase != "LOBBY":
            await interaction.response.send_message("The game has already started.", ephemeral=True)
            return
        if len(state.players) >= self.max_players:
            async with AsyncSessionLocal() as session:
                await limit_hit_repo.record(
                    session    = session,
                    guild_id   = interaction.guild_id,
                    user_id    = interaction.user.id,
                    channel_id = interaction.channel_id,
                    limit_type = "max_players",
                )
            await interaction.response.send_message(
                f"The lobby is full ({self.max_players} players max).", ephemeral=True
            )
            return

        joined = await add_player(state, interaction.user.id, interaction.user.display_name)
        if not joined:
            await interaction.response.send_message("You're already in the lobby!", ephemeral=True)
            return

        self.state = state
        await interaction.response.edit_message(
            embed=build_lobby_embed(state, self.max_players, self.selected_genre_key), view=self
        )

    @discord.ui.button(label="Start Game", style=discord.ButtonStyle.primary, emoji="▶️", row=2)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        state = await session_manager.load(self.state.channel_id)
        if state is None:
            await interaction.response.send_message("This lobby no longer exists.", ephemeral=True)
            return

        ok, reason = can_start(state, interaction.user.id, self.max_players)
        if not ok:
            await interaction.response.send_message(reason, ephemeral=True)
            return

        # Disable everything so no one can join or change genre mid-start
        for item in self.children:
            item.disabled = True

        genre_name = genre_display_name(self.selected_genre_key)
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="⏳  Starting Game…",
                description=(
                    f"Setting: **{genre_name}**\n\n"
                    "Generating your unique murder case. This takes a few seconds."
                ),
                color=discord.Color.dark_grey(),
            ),
            view=self,
        )
        self.started = True
        self.stop()
        self.state = state
