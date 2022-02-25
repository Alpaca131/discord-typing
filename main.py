from abc import ABC

import discord
from discord.commands import Option
from discord.ext import commands

import envs
import game_funcs
from classes import button_classes
from classes.game_info import GameInfo
from google_input import FilterRuleTable, GoogleInput

games = {}


class Bot(commands.Bot, ABC):
    def __init__(self):
        super().__init__()


table = FilterRuleTable.from_file("google_ime_default_roman_table.txt")
gi = GoogleInput(table)

bot = Bot()


@bot.event
async def on_ready():
    print("logged in")


@bot.slash_command(name="ゲーム開始", guild_ids=[736242858830463117])
async def game_start(
        ctx: discord.ApplicationContext,
        word_count: Option(int, "問題の文字数を入力", name="文字数", min_value=2, max_value=14)
):
    if game_funcs.is_game_exists(channel_id=ctx.channel_id):
        await ctx.respond("進行中のゲームがあります。先にそちらを終了して下さい。")
        return
    game = GameInfo(channel_id=ctx.channel_id, word_count=word_count)
    game_funcs.save_game(game)
    view = discord.ui.View(timeout=None)
    view.add_item(button_classes.GameJoinButton())
    view.add_item(button_classes.GameLeaveButton())
    view.add_item(button_classes.GameStartButton())
    view.add_item(button_classes.GameQuitButton())

    embed = discord.Embed(title="参加する人は参加ボタンを押して下さい。\n用意が出来たらスタートボタンでゲームを開始できます。\n\n中止ボタンでゲームを中止出来ます。",
                          color=discord.Color.blue())

    await ctx.respond(embed=embed, view=view)


bot.run(envs.TOKEN)
