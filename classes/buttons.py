import discord
from discord.ui import Button
from game_info import GameInfo
from main import get_game, save_game, remove_game


class GameJoinButton(Button):
    def __init__(self):
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


class GameLeaveButton(Button):
    def __init__(self):
        super().__init__(
            label="抜ける",
            style=discord.enums.ButtonStyle.secondary
        )

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        channel_id = interaction.channel_id
        game: GameInfo = get_game(channel_id)
        game.remove_player(user.id)
        save_game(game)


class GameStartButton(Button):
    def __init__(self):
        super().__init__(
            label="ゲーム開始",
            style=discord.enums.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        channel_id = interaction.channel_id
        game: GameInfo = get_game(channel_id)
        """
        既存のボタンを無効化
        """


class GameQuitButton(Button):
    def __init__(self):
        super().__init__(
            label="中止",
            style=discord.enums.ButtonStyle.primary
        )

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        channel_id = interaction.channel_id
        game: GameInfo = get_game(channel_id)
        game.end_game()
        remove_game(game)
        """
        既存のボタンを無効化
        """
