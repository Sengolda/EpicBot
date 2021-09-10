import discord
import datetime
import pytz
from discord.ext import commands
from utils.bot import EpicBot
from config import MAIN_COLOR
from utils.time import convert_int_to_weekday
from utils.custom_checks import mutual_guild
from typing import List, Optional, Union


stream_schedule = {
    0: True,  # Monday
    1: False,  # Tuesday
    2: True,  # Wednesday
    3: True,  # Thrusday
    4: False,  # Friday
    5: True,  # Saturday
    6: False  # Sunday
}
live_text = "Ramaziz will be live today!"
not_live_text = "Ramaziz will not be live today!"
be_sure = "Be sure to check <#762550256918724640> in case of any stream cancellations!"


SexContext = Union[commands.Context, discord.Interaction]


slash_cmds = {}


def slash_cmd(*, name: Optional[str] = None, guild_ids: List[int]):
    def inner_deco(func):
        cmd_name = name or func.__name__
        slash_cmds.update({cmd_name: {'func': func, 'guild_ids': guild_ids}})
        return func
    return inner_deco


class RamTimeView(discord.ui.View):
    def __init__(self, author_id: int, time_embed: discord.Embed, current_time: datetime.datetime):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.time_embed = time_embed
        self.current_time = current_time

    @discord.ui.button(label="Time", emoji='⏰', style=discord.ButtonStyle.blurple, disabled=True)
    async def time(self, button: discord.ui.Button, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = False
        button.disabled = True
        await interaction.message.edit(embed=self.time_embed, view=self)

    @discord.ui.button(label="Stream Schedule", emoji='📝', style=discord.ButtonStyle.blurple)
    async def stream_schedule(self, button: discord.ui.Button, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = False
        button.disabled = True
        stream_schedule_embed = discord.Embed(
            title="Stream Schedule",
            description="Ramaziz's twitch stream schedule: **[Go follow!](https://twitch.tv/ramaziz)**",
            color=MAIN_COLOR
        ).add_field(
            name="Current Stream",
            value=f"{live_text if stream_schedule[self.current_time.weekday()] else not_live_text}\n{be_sure}",
            inline=False
        ).add_field(
            name="Schedule",
            value='\n'.join([f"**{convert_int_to_weekday(i)}** • {stream_schedule[i]}" for i in stream_schedule]),
            inline=False
        )
        await interaction.message.edit(embed=stream_schedule_embed, view=self)

    @discord.ui.button(label="Close menu", emoji='⏹️', style=discord.ButtonStyle.danger)
    async def close(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.message.delete()

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id == self.author_id:
            return True
        else:
            return await interaction.response.send_message("Not your command o_o", ephemeral=True)


class PrivateCmds(commands.Cog):
    def __init__(self, client: EpicBot):
        self.client = client

    @commands.command(
        aliases=['ram-time', 'time-ram', 'timeram', 'time_ram', 'ramaziztime', 'ramaziz_time', 'ramaziz-time', 'ramtime'],
        help="Ever wonder what time is it for Ramaziz?"
    )
    @mutual_guild(719157704467152977)
    @slash_cmd(name='ramtime', guild_ids=[719157704467152977, 749996055369875456])
    async def ram_time(self, ctx: SexContext):
        dt_utc = datetime.datetime.now(tz=pytz.UTC)
        dt_nzt = dt_utc.astimezone(pytz.timezone("NZ"))

        time_embed = discord.Embed(title="⏰  Ram Time", color=MAIN_COLOR)
        time_embed.add_field(name="Time", value=f"{dt_nzt.strftime('%I : %M : %S %p')}", inline=False)
        time_embed.add_field(name="Date", value=f"{convert_int_to_weekday(dt_nzt.weekday())} | {dt_nzt.day} / {dt_nzt.month} / {dt_nzt.year}", inline=False)

        if isinstance(ctx, commands.Context):
            view = RamTimeView(ctx.author.id, time_embed, dt_nzt)
            await ctx.reply(embed=time_embed, view=view)
        else:
            view = RamTimeView(ctx.user.id, time_embed, dt_nzt)
            await ctx.response.send_message(embed=time_embed, view=view)

    @slash_cmd(guild_ids=[746202728031584358])
    async def kitten(self, ctx: SexContext):
        await ctx.response.send_message("Don't tell kitten 👀 but dogs are kinda cute uwu", ephemeral=True)

    @commands.Cog.listener("on_interaction")
    async def private_slash_cmds(self, interaction: discord.Interaction):
        data = interaction.data
        inter_type = data.get('type')
        # checking if it's a slash cmd or not
        # https://discord.com/developers/docs/interactions/application-commands#application-command-object-application-command-types
        if inter_type is None:
            return
        if int(inter_type) != 1:
            return
        # checking if the slash cmd is in the slash cmds dict
        if data.get('name') not in slash_cmds:
            return
        slash_cmd = slash_cmds[data.get('name')]
        if interaction.guild_id not in slash_cmd['guild_ids']:
            return
        await slash_cmd['func'](self, interaction)


def setup(client: EpicBot):
    client.add_cog(PrivateCmds(client))
