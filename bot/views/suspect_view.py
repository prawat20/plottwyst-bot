from __future__ import annotations
"""
Paginated suspect profile viewer.

Replaces 6 individual suspect embeds with a single interactive message.
All players share the same navigation — flipping is a collaborative act.
Timeout matches the game TTL so buttons stay active throughout.
"""
import discord
import config


class SuspectFilesView(discord.ui.View):
    def __init__(self, suspects: list[dict]):
        super().__init__(timeout=float(config.GAME_STATE_TTL))
        self.suspects = suspects
        self.page     = 0
        self._sync_buttons()

    # ── Embed builder ─────────────────────────────────────────────────────────

    def build_embed(self) -> discord.Embed:
        s     = self.suspects[self.page]
        total = len(self.suspects)
        embed = discord.Embed(
            title=f"🕵️  Suspect {self.page + 1} of {total}  ·  {s['name']}",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Relation to Victim", value=s["relation"],          inline=True)
        embed.add_field(name="Personality",         value=s["trait"],             inline=True)
        embed.add_field(name="Last Seen",           value=s["last_seen"],          inline=True)
        embed.add_field(name="Motive",              value=s["motive"],             inline=False)
        embed.add_field(name="Their Statement",     value=f'*"{s["alibi"]}"*',    inline=False)
        embed.set_footer(
            text=f"◀ / ▶ to browse all {total} suspects  ·  Keep this message handy for reference"
        )
        return embed

    # ── Button sync ───────────────────────────────────────────────────────────

    def _sync_buttons(self):
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page == len(self.suspects) - 1
        # Update counter label
        self.counter_btn.label = f"{self.page + 1} / {len(self.suspects)}"

    # ── Buttons ───────────────────────────────────────────────────────────────

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="1 / 6", style=discord.ButtonStyle.secondary, disabled=True)
    async def counter_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Non-interactive — just a page counter display
        await interaction.response.defer()

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self._sync_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)
