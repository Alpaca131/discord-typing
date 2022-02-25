import discord
from discord.ui import Button
from classes.game_info import GameInfo
import game_funcs


class GameJoinButton(Button):
    def __init__(self):
        super().__init__(
            label="参加",
            style=discord.enums.ButtonStyle.success
        )

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        channel_id = interaction.channel_id
        game: GameInfo = game_funcs.get_game(channel_id)
        if user.id in game.player_list:
            return
        game.add_player(member_id=user.id)
        game_funcs.save_game(game)
        await interaction.response.send_message(f"ゲームに参加しました！", ephemeral=True)


class GameLeaveButton(Button):
    def __init__(self):
        super().__init__(
            label="抜ける",
            style=discord.enums.ButtonStyle.secondary
        )

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        channel_id = interaction.channel_id
        game: GameInfo = game_funcs.get_game(channel_id)
        if user.id not in game.player_list:
            return
        game.remove_player(user.id)
        game_funcs.save_game(game)
        await interaction.response.send_message(f"ゲームから抜けました。", ephemeral=True)


class GameStartButton(Button):
    def __init__(self):
        super().__init__(
            label="ゲーム開始",
            style=discord.enums.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        channel_id = interaction.channel_id
        game: GameInfo = game_funcs.get_game(channel_id)
        await interaction.response.send_message(f"ゲームを開始します！", ephemeral=False)
        await interaction.message.delete()


class GameQuitButton(Button):
    def __init__(self):
        super().__init__(
            label="中止",
            style=discord.enums.ButtonStyle.danger
        )

    async def callback(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id
        game: GameInfo = game_funcs.get_game(channel_id)
        game.end_game()
        game_funcs.remove_game(game)
        await interaction.response.send_message(f"ゲームを中止しました。", ephemeral=False)
        await interaction.message.delete()
