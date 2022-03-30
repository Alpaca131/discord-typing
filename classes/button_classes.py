import discord
from discord.ui import Button

import games_func
from classes.game_class import GameInfo


class GameJoinButton(Button):
    def __init__(self):
        super().__init__(
            label="参加",
            style=discord.enums.ButtonStyle.success
        )

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        channel_id = interaction.channel_id
        game: GameInfo = games_func.get_game(channel_id)
        if user.id in game.player_list:
            return
        game.add_player(member_id=user.id)
        games_func.save_game(game)
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
        game: GameInfo = games_func.get_game(channel_id)
        if user.id not in game.player_list:
            return
        game.remove_player(user.id)
        games_func.save_game(game)
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
        game: GameInfo = games_func.get_game(channel_id)
        for user_id in game.player_list:
            game.start_answering(user_id)
        question = game.get_next_question()
        game.save()
        view = discord.ui.View(timeout=None)
        view.add_item(NextQuestionButton())
        view.add_item(GameQuitButton())
        embed = discord.Embed(title=f"問題1：{question}",
                              color=discord.Color.green())
        await interaction.response.send_message(f"ゲームを開始します！", ephemeral=False)
        await interaction.channel.send(embed=embed, view=view)
        await interaction.message.delete()


class GameQuitButton(Button):
    def __init__(self):
        super().__init__(
            label="中止",
            style=discord.enums.ButtonStyle.danger
        )

    async def callback(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id
        game: GameInfo = games_func.get_game(channel_id)
        game.end_game()
        games_func.remove_game(game)
        await interaction.response.send_message(f"ゲームを中止しました。", ephemeral=False)


class NextQuestionButton(Button):
    def __init__(self):
        super().__init__(
            label="次の問題へ",
            style=discord.enums.ButtonStyle.success
        )

    async def callback(self, interaction: discord.Interaction):
        channel_id = interaction.channel_id
        game: GameInfo = games_func.get_game(channel_id)
        q_kanji = game.get_next_question()
        q_number = game.question_index + 1
        embed = discord.Embed(title=f"問題{q_number}：{q_kanji}", color=discord.Color.green())
        game.save()
        view = discord.ui.View(timeout=None)
        view.add_item(NextQuestionButton())
        view.add_item(GameQuitButton())
        await interaction.channel.send(embed=embed, view=view)
