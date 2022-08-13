import asyncio
from abc import ABC

import discord
from discord.commands import Option
from discord.ext import commands

from utils import games_func, envs, rankings
from classes import button_classes
from classes.ranking_class import *
from classes.game_class import GameManager


class Bot(commands.Bot, ABC):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())


bot = Bot()


@bot.event
async def on_ready():
    print("logged in")


@bot.slash_command(name="help")
async def help_command(ctx: discord.ApplicationContext):
    embed = discord.Embed(title="タイピングBot", description="問題は寿司打の物を利用しています。\n**ランキングは10文字の問題を解くと対象になります。**",
                          color=discord.Color.green())
    embed.add_field(name="/ゲーム開始", value="ゲームを開始します。", inline=False)
    embed.add_field(name="/サーバーランキング", value="サーバー内でのランキングを表示します。", inline=False)
    embed.add_field(name="/グローバルランキング", value="全利用者中のランキングを表示します。", inline=False)
    await ctx.respond(embed=embed, ephemeral=True)


@bot.slash_command(name="ゲーム開始")
async def game_start(
        ctx: discord.ApplicationContext,
        word_count: Option(str, "問題の文字数を選択", name="文字数", choices=[str(i) for i in range(2, 15)])  # noqa
):
    if games_func.is_game_exists(channel_id=ctx.channel_id):
        await ctx.respond("進行中のゲームがあります。先にそちらを終了して下さい。")
        return
    word_count = int(word_count)
    game = GameManager(channel_id=ctx.channel_id, word_count=word_count)
    game.add_player(member_id=ctx.author.id)
    game.save()
    view = discord.ui.View(timeout=None)
    view.add_item(button_classes.GameJoinButton())
    view.add_item(button_classes.GameLeaveButton())
    view.add_item(button_classes.GameStartButton())
    view.add_item(button_classes.GameQuitButton())

    embed = discord.Embed(title="参加する人は参加ボタンを押して下さい。\n"
                                "用意が出来たらスタートボタンでゲームを開始できます。\n\n"
                                "中止ボタンでゲームを中止出来ます。",
                          color=discord.Color.blue())
    embed.add_field(name="文字数", value=f"{word_count}文字")
    embed.add_field(name="参加者", value=ctx.author.display_name)
    await ctx.respond(embed=embed, view=view)


@bot.slash_command(name="サーバーランキング")
async def global_ranking(ctx: discord.ApplicationContext):
    ranking: GuildRanking = await rankings.get_guild_ranking(guild_id=ctx.guild.id)
    all_records: dict = ranking.get_all_records()
    embed = discord.Embed(title="このサーバーでの順位", color=discord.Color.green(),
                          description=f"文字数：{ranking.word_count}文字")
    for user_id in all_records:
        rank = list(all_records.keys()).index(user_id) + 1
        member = ctx.guild.get_member(user_id)
        embed.add_field(name=f"{rank}位 {member.display_name}#{member.discriminator}", value=f"{all_records[user_id]}秒")
    await ctx.respond(embed=embed)


@bot.slash_command(name="全体ランキング")
async def global_ranking(ctx: discord.ApplicationContext):
    ranking: GlobalRanking = await rankings.get_global_ranking()
    all_records = ranking.get_all_records()
    embed = discord.Embed(title="全サーバーでの順位", color=discord.Color.green(),
                          description=f"文字数：{ranking.word_count}文字")
    for user_id in all_records:
        rank = list(all_records.keys()).index(user_id) + 1
        user = bot.get_user(user_id)
        embed.add_field(name=f"{rank}位 {user.name}#{user.discriminator}", value=f"{all_records[user_id]}秒")
    await ctx.respond(embed=embed)


@bot.event
async def on_message(message: discord.Message):
    if not games_func.is_game_exists(channel_id=message.channel.id):
        return
    if message.author.bot:
        return  # ボットは無視
    game: GameManager = games_func.get_game(channel_id=message.channel.id)
    # 答え合わせ
    is_correct, is_last_question = await check_answer(message, game)
    # 正解の場合の処理
    if not is_correct:
        return
    # 全プレイヤーが回答済みの場合
    if game.is_all_player_answered():
        # 最後の問題の場合は全体の集計結果を表示
        if is_last_question:
            await send_all_aggregated_result(message, game)
        # そうでない場合は次の問題に移行
        else:
            await move_to_next_question(message, game)


async def send_all_aggregated_result(message: discord.Message, game: GameManager):
    embed = discord.Embed(title="全員の平均タイム", color=discord.Color.orange())
    players_sorted_time, players_not_answered_count = game.aggregate_all_result()
    ranking = 0
    print(players_sorted_time)
    for t in players_sorted_time:
        user_id = t[0]
        average_time = t[1]
        ranking += 1
        member = message.guild.get_member(user_id)
        embed.add_field(name=f"{ranking}位 {member.name}",
                        value=f"{average_time:.03f}秒\n未回答の問題：{players_not_answered_count[user_id]}問",
                        inline=False)
    await message.channel.send(embed=embed)


async def check_answer(message: discord.Message, game: GameManager):
    if not game.is_answering(user_id=message.author.id):
        return
    is_correct, elapsed_time = game.submit_answer(user_id=message.author.id, user_answer=message.content)
    game.save()
    is_last_question = False
    if not is_correct:
        embed = discord.Embed(title="不正解です。", color=discord.Color.red())
        await message.channel.send(embed=embed)
    else:
        embed = discord.Embed(title="正解です！",
                              description=f"回答時間：{elapsed_time}秒", color=discord.Color.green())
        await message.channel.send(embed=embed)

        is_last_question = game.question_index == 9
        if is_last_question:
            average_time, not_answered_question_count = game.aggregate_user_result(user_id=message.author.id)
            embed = discord.Embed(title=f"あなたの平均タイムは{average_time:.03f}秒です。",
                                  description=f"未回答の問題：{not_answered_question_count}問",
                                  color=discord.Color.greyple())
            await message.channel.send(embed=embed)
    return is_correct, is_last_question


async def move_to_next_question(message: discord.Message, game: GameManager):
    view = discord.ui.View(timeout=None)
    view.add_item(button_classes.GameQuitButton())
    embed = discord.Embed(title="全員が答え合わせを終了しました。\n2秒後に次の問題に進みます。", description="中止ボタンでゲームを中止出来ます。")
    await message.channel.send(embed=embed, view=view)
    await asyncio.sleep(2)
    question = game.get_next_question()
    question_number = game.question_index + 1
    embed = discord.Embed(title=f"問題{question_number}：{question}", color=discord.Color.green())
    for user_id in game.player_list:
        game.start_answering(user_id=user_id)
    game.save()
    view = discord.ui.View(timeout=None)
    view.add_item(button_classes.NextQuestionButton())
    view.add_item(button_classes.GameQuitButton())
    await message.channel.send(embed=embed, view=view)


try:
    bot.run(envs.TOKEN)
finally:
    pass
