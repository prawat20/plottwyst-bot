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

def _build_htp_pages() -> list[dict]:
    return [
        {
            "title": "📖  How to Play — Overview",
            "description": (
                "**Plottwyst** is a cooperative murder mystery game for Discord.\n\n"
                "A crime has been committed. You and your fellow detectives must study "
                "the suspects, gather clues across 4 rounds, and name the murderer "
                "before the trail goes cold.\n\n"
                "**Win condition:** Correctly identify the murderer in the final guess.\n"
                "**Lose condition:** Vote out the murderer mid-game (Classic), or fail to name them in the final guess (Silent Investigation).\n\n"
                "⚠️ **Every case contains a Plottwyst** — a deliberate misdirection "
                "built into the evidence from the very first clue. "
                "The opening evidence may point confidently in the wrong direction. "
                "Trust the clues, but question what they're really telling you."
            ),
            "fields": [
                ("🎮  Start a Game", "`/lobby` → host clicks ⚙️ Settings → players join → Start", False),
                ("⏱️  Game Length", "~20 minutes", True),
                ("👥  Players", "2–5 (free)  ·  2–10 (premium)", True),
            ],
            "footer": "Page 1 / 5  ·  Use the buttons below to navigate",
            "color": discord.Color.dark_blue(),
        },
        {
            "title": "🔴  How to Play — The Crime Scene",
            "description": (
                "Once the game begins, the full case is revealed:\n\n"
                "**📍 Setting** — The location and era of the crime.\n"
                "**💀 Victim** — Who died, their background, and what secrets they kept.\n"
                "**🕵️ Suspects** — Six characters, each with a relation to the victim, "
                "a motive, a last known location, and a personal alibi statement.\n"
                "**🔎 Opening Clues** — Three pieces of initial evidence to start your investigation.\n\n"
                "Read every suspect profile carefully before discussion begins — "
                "the details in their background and alibi matter more than they appear."
            ),
            "fields": [
                (
                    "💡  Detective Tip",
                    "Don't anchor too early. The opening clues are designed to build a convincing "
                    "picture — but that picture may be exactly what the killer wants you to see. "
                    "Cross-reference every clue against every profile.",
                    False,
                ),
            ],
            "footer": "Page 2 / 5",
            "color": discord.Color.dark_red(),
        },
        {
            "title": "💬  How to Play — Discussion & Voting",
            "description": (
                "There are **4 rounds**. Each round has three stages:\n\n"
                "**1. Discussion** — Talk freely in chat. Share theories, challenge alibis, "
                "and cross-reference clues against suspect profiles. "
                "The timer runs — use the time.\n\n"
                "**2. Voting** — Each player votes to **clear** one suspect they're "
                "confident is innocent. The suspect with the most votes is eliminated "
                "from the pool. No majority = no elimination, game continues.\n\n"
                "**3. New Clue** — A fresh piece of evidence is revealed. "
                "Later clues are more precise — pay close attention to rounds 3 and 4."
            ),
            "fields": [
                (
                    "🗡️  Classic Mode (default)",
                    "If your team votes out the **actual murderer**, the game ends immediately — "
                    "the killer escapes. There is no second chance. "
                    "Be certain before you clear someone.",
                    False,
                ),
                (
                    "🔍  Silent Investigation Mode",
                    "The game **always runs to the final guess** regardless of who is voted out. "
                    "Cleared suspects can't be named in the final guess — if you clear the murderer "
                    "mid-game they walk free, but you won't know until the resolution reveal. "
                    "Host switches modes in ⚙️ Settings before the game starts.",
                    False,
                ),
            ],
            "footer": "Page 3 / 5",
            "color": discord.Color.blue(),
        },
        {
            "title": "🗳️  How to Play — How Voting Works",
            "description": (
                "Voting is your tool for **narrowing the suspect pool** round by round.\n\n"
                "**Step-by-step:**\n"
                "① Click a suspect's name — the one you're sure is **NOT** the murderer\n"
                "② A private confirmation appears — only you can see it\n"
                "③ Confirm to lock your vote in\n"
                "④ If a strict majority of players agree, that suspect is cleared\n\n"
                "**No majority reached?** No one is eliminated — the next clue is revealed "
                "and you move on.\n\n"
                "**📋 Case File button** — visible during every voting round. "
                "Click it for a private digest of all suspects and every clue revealed so far. "
                "Use it to refresh your memory without scrolling up."
            ),
            "fields": [
                (
                    "💡  Strategy",
                    "Coordinate during discussion — if your team splits votes across two suspects, "
                    "neither gets eliminated. Agree on one target before voting opens.",
                    False,
                ),
            ],
            "footer": "Page 4 / 5",
            "color": discord.Color.orange(),
        },
        {
            "title": "🎯  How to Play — Final Guess & Resolution",
            "description": (
                "After all 4 rounds, every detective gets **one final guess**.\n\n"
                "**Final Guess:**\n"
                "Choose who you believe is the murderer from the remaining suspects. "
                "Your answer is private — no one sees it until the full reveal.\n\n"
                "**Resolution:**\n"
                "Every detective's verdict is unsealed one by one. "
                "Then the full truth is revealed — the murderer's identity, their real motive, "
                "how they committed the crime, and the **Plottwyst**: "
                "exactly how the misdirection was constructed to fool you.\n\n"
                "Every detective who guessed correctly wins 🏆\n"
                "Results are saved automatically — check `/stats` or `/leaderboard` anytime."
            ),
            "fields": [
                (
                    "🎭  Did the Plottwyst fool you?",
                    "After each game you can rate the case and tell us whether the misdirection "
                    "worked. That feedback shapes future cases.",
                    False,
                ),
            ],
            "footer": "Page 5 / 5  ·  Good luck, Detective.",
            "color": discord.Color.dark_purple(),
        },
    ]


def _build_htp_embed(page: int) -> discord.Embed:
    data   = _build_htp_pages()[page]
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
        self.next_btn.disabled = self.page == len(_build_htp_pages()) - 1

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
        free_server_limit = TIERS["free"][Feature.DAILY_GAME_LIMIT]
        free_user_limit   = TIERS["free"][Feature.USER_DAILY_GAME_LIMIT]
        free_players      = TIERS["free"][Feature.MAX_PLAYERS]

        embed = discord.Embed(
            title="🔍  About Plottwyst",
            description=(
                "**Plottwyst** is a murder mystery game for Discord.\n\n"
                "Every case is uniquely generated — different victims, suspects, motives, "
                "and clues every single time. No two investigations are ever the same.\n\n"
                "Every case also contains a **Plottwyst** — a deliberate misdirection "
                "built into the evidence from clue one. Your job is to see through it."
            ),
            color=discord.Color.dark_blue(),
        )
        embed.add_field(
            name="How It Works",
            value=(
                "Plottwyst generates original murder mysteries across genres — "
                "Victorian England, 1920s noir, modern corporate thriller, and more. "
                "Evidence builds over 4 rounds, each clue narrowing the field "
                "until one final guess decides the case."
            ),
            inline=False,
        )
        embed.add_field(
            name="🆓  Free Tier",
            value=(
                f"· Up to **{free_players} players** per game\n"
                f"· **{free_server_limit} games/day** per server\n"
                f"· **{free_user_limit} games/day** per player\n"
                f"· Full leaderboard & personal stats\n"
                f"· Unique mysteries every game"
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
