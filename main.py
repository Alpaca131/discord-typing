from abc import ABC

import discord
from discord.ext import commands
from discord.ui import InputText, Modal, Button
from classes.game_info import GameInfo
import envs

games: dict[int: GameInfo] = {}


class Bot(commands.Bot, ABC):
    def __init__(self):
        super().__init__()

bot = Bot()


class GameJoinButton(Button):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            label="参加",
            style=discord.enums.ButtonStyle.success
        )

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        channel_id = interaction.channel_id
        game: GameInfo = get_game(channel_id)
        game.add_player(user.id)
        save_game(game)
        await interaction.response.send_message(f"ゲームに参加しました！", ephemeral=True)


def get_game(channel_id: int):
    return games.get(channel_id)

def save_game(game: GameInfo):
    channel_id = game.channel_id
    games[channel_id] = GameInfo

def remove_game(game: GameInfo):
    channel_id = game.channel_id
    games.pop(channel_id, None)

@bot.event
async def on_ready():
    print("logged in")


@bot.slash_command(name="ゲーム開始", guild_ids=[736242858830463117, 813733682384470037])
async def game_start(ctx: discord.ApplicationContext):
    await ctx.respond(type=discord, "Hello!")

bot.run(envs.TOKEN)
