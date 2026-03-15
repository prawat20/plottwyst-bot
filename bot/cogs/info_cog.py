from __future__ import annotations
"""
Info cog — /howtoplay, /about, /commands
User-facing onboarding and information commands.
"""
import discord
from discord import app_commands
from discord.ext import commands

from tiers.entitlements import TIERS, Feature


# ── How-To-Play pages ────────────────────────────────────────────────────────

_HTP_PAGES = [
    {
        "title": "📖  How to Play — Overview",
        "description": (
            "**Plottwyst** is a cooperative murder mystery game for Discord.\n\n"
            "A crime has been committed. You and your fellow detectives must study "
            "the suspects, gather clues across 4 rounds, and name the murderer "
            "before the trail goes cold.\n\n"
            "**Win condition:** Correctly identify the murderer in the final guess.\n"
            "**Lose condition:** Accidentally vote out the murderer during a round — "
            "and *nobody wins*."
        ),
        "fields": [
            ("🎮  Start a Game", "`/lobby` → Join → Host clicks Start Game", False),
            ("⏱️  Game Length", "~15–25 minutes", True),
            ("👥  Players", "1–5 (free)  ·  1–10 (premium)", True),
        ],
        "footer": "Page 1 / 5  ·  Use the buttons below to navigate",
        "color": discord.Color.dark_blue(),
    },
    {
        "title": "🔴  How to Play — The Crime Scene",
        "description": (
            "Once the game begins, Plottwyst reveals the full case:\n\n"
            "**📍 Setting** — The location and era of the crime.\n"
            "**💀 Victim** — Who died, and their background.\n"
            "**⚡ Twist** — An unexpected detail that changes the picture.\n"
            "**🕵️ Suspects** — Six characters, each with a relation to the victim, "
            "a motive, a last known location, and a personal statement.\n"
            "**🔎 Opening Clues** — Your first pieces of hard evidence.\n\n"
            "Take your time — read every profile before the discussion starts."
        ),
        "fields": [
            (
                "💡  Detective Tip",
                "The murderer's alibi will have subtle inconsistencies. "
                "Cross-reference their statement against the clues.",
                False,
            ),
        ],
        "footer": "Page 2 / 5",
        "color": discord.Color.dark_red(),
    },
    {
        "title": "💬  How to Play — Discussion Rounds",
        "description": (
            "There are **4 rounds**. Each round has three stages:\n\n"
            "**1. Discussion** — The timer runs while you talk in chat. "
            "Share theories, challenge alibis, and build your case.\n\n"
            "**2. Voting** — Clear a suspect you're confident is innocent. "
            "The person with the most votes is eliminated from the suspect pool.\n\n"
            "**3. New Clue** — Fresh evidence is revealed to help you close in."
        ),
        "fields": [
            (
                "⚠️  Critical Rule",
                "If the eliminated suspect turns out to be the murderer, "
                "**the round is forfeit and nobody wins it.** Choose carefully.",
                False,
            ),
        ],
        "footer": "Page 3 / 5",
        "color": discord.Color.blue(),
    },
    {
        "title": "🗳️  How to Play — Voting",
        "description": (
            "Voting is your tool for **clearing innocent suspects** from the pool.\n\n"
            "**Step-by-step:**\n"
            "① Click the name of the suspect you're sure is **NOT** the murderer.\n"
            "② A private confirmation prompt appears — only you can see it.\n"
            "③ Confirm your vote to lock it in.\n"
            "④ If a majority of players agree, that suspect is eliminated.\n\n"
            "**No majority?** No one is eliminated — you simply move on to the next clue.\n\n"
            "**Strategy:** Coordinate with your team during discussion so your "
            "votes land on the same innocent suspect."
        ),
        "fields": [
            (
                "💡  Tip",
                "You can only vote once per round, and you can't change it after confirming. Think before you click.",
                False,
            ),
        ],
        "footer": "Page 4 / 5",
        "color": discord.Color.orange(),
    },
    {
        "title": "🎯  How to Play — Final Guess & Resolution",
        "description": (
            "After all rounds, every player gets **one final guess**.\n\n"
            "**Final Guess:**\n"
            "Select who you believe is the murderer from the remaining suspects. "
            "Your choice is private — only the resolution will reveal who was right.\n\n"
            "**Resolution:**\n"
            "The full truth comes out — the murderer's real motive, how the crime "
            "was committed, and the clever red herring that was planted to mislead you.\n\n"
            "Every detective who guessed correctly is crowned a **winner** 🏆\n"
            "Your results are saved — check `/stats` or `/leaderboard` anytime."
        ),
        "fields": [
            (
                "🔁  Replay Value",
                "Every case is AI-generated — new suspects, motives, and clues each time. No two games are alike.",
                False,
            ),
        ],
        "footer": "Page 5 / 5  ·  Good luck, Detective!",
        "color": discord.Color.dark_purple(),
    },
]


def _build_htp_embed(page: int) -> discord.Embed:
    data   = _HTP_PAGES[page]
    embed  = discord.Embed(
        title=data["title"],
        description=data["description"],
        color=data["color"],
    )
    for name, value, inline in data.get("fields", []):
        embed.add_field(name=name, value=value, inline=inline)
    embed.set_footer(text=data["footer"])
    return embed


class HowToPlayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.page = 0
        self._sync_buttons()

    def _sync_buttons(self):
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page == len(_HTP_PAGES) - 1

    @discord.ui.button(label="◀  Previous", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self._sync_buttons()
        await interaction.response.edit_message(embed=_build_htp_embed(self.page), view=self)

    @discord.ui.button(label="Next  ▶", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self._sync_buttons()
        await interaction.response.edit_message(embed=_build_htp_embed(self.page), view=self)


# ── Info Cog ─────────────────────────────────────────────────────────────────

class InfoCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── /howtoplay ────────────────────────────────────────────────────────────

    @app_commands.command(
        name="howtoplay",
        description="Step-by-step guide to playing Plottwyst — great for new detectives.",
    )
    async def howtoplay(self, interaction: discord.Interaction) -> None:
        view = HowToPlayView()
        await interaction.response.send_message(
            embed=_build_htp_embed(0), view=view, ephemeral=True
        )

    # ── /about ────────────────────────────────────────────────────────────────

    @app_commands.command(
        name="about",
        description="Learn about Plottwyst — the AI-powered murder mystery game.",
    )
    async def about(self, interaction: discord.Interaction) -> None:
        free_limit   = TIERS["free"][Feature.DAILY_GAME_LIMIT]
        free_players = TIERS["free"][Feature.MAX_PLAYERS]

        embed = discord.Embed(
            title="🔍  About Plottwyst",
            description=(
                "**Plottwyst** is an AI-powered murder mystery game for Discord.\n\n"
                "Every case is uniquely generated — different victims, suspects, motives, "
                "and clues every single time. No two investigations are ever the same."
            ),
            color=discord.Color.dark_blue(),
        )
        embed.add_field(
            name="How It Works",
            value=(
                "Plottwyst uses Google Gemini to craft original murder mysteries across "
                "genres like Victorian England, 1920s noir, and corporate intrigue. "
                "Evidence drips in over 4 rounds — building tension until the final reveal."
            ),
            inline=False,
        )
        embed.add_field(
            name="🆓  Free Tier",
            value=(
                f"· Up to **{free_players} players** per game\n"
                f"· **{free_limit} games** per day\n"
                f"· Full leaderboard & personal stats\n"
                f"· AI-generated mysteries"
            ),
            inline=True,
        )
        embed.add_field(
            name="⭐  Premium",
            value=(
                "· Up to **10 players** per game\n"
                "· **Unlimited** daily games\n"
                "· Private DM clues *(coming soon)*\n"
                "· Murderer Among Players *(coming soon)*"
            ),
            inline=True,
        )
        embed.add_field(
            name="\u200b",  # invisible spacer
            value="\u200b",
            inline=False,
        )
        embed.add_field(
            name="Quick Commands",
            value=(
                "`/lobby` — Start a new game\n"
                "`/howtoplay` — Step-by-step guide\n"
                "`/stats` — Your detective record\n"
                "`/leaderboard` — Server rankings\n"
                "`/premium info` — Upgrade details"
            ),
            inline=False,
        )
        embed.set_footer(text="Plottwyst  ·  Every case is a new story.")
        await interaction.response.send_message(embed=embed)

    # ── /commands ─────────────────────────────────────────────────────────────

    @app_commands.command(
        name="commands",
        description="See all available Plottwyst slash commands.",
    )
    async def commands_list(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="📋  Plottwyst — All Commands",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="🎮  Game",
            value="`/lobby` — Create a new murder mystery lobby",
            inline=False,
        )
        embed.add_field(
            name="📊  Stats",
            value=(
                "`/stats` — Your personal detective record\n"
                "`/leaderboard` — Top detectives in this server"
            ),
            inline=False,
        )
        embed.add_field(
            name="ℹ️  Info",
            value=(
                "`/howtoplay` — Step-by-step new player guide\n"
                "`/about` — What is Plottwyst?\n"
                "`/commands` — This list"
            ),
            inline=False,
        )
        embed.add_field(
            name="⭐  Premium",
            value=(
                "`/premium info` — What's included in premium\n"
                "`/premium activate` — Activate a premium key"
            ),
            inline=False,
        )
        embed.set_footer(text="New to the game? Start with /howtoplay")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(InfoCog(bot))
