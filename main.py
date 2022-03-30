import asyncio
from abc import ABC

import discord
from discord.commands import Option
from discord.ext import commands

import envs
import games_func
from classes import button_classes
from classes.game_class import GameInfo


class Bot(commands.Bot, ABC):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())


bot = Bot()


@bot.event
async def on_ready():
    print("logged in")


@bot.slash_command(name="ゲーム開始", guild_ids=[736242858830463117])
async def game_start(
        ctx: discord.ApplicationContext,
        word_count: Option(str, "問題の文字数を選択", name="文字数", choices=[str(i) for i in range(2, 15)])  # noqa
):
    if games_func.is_game_exists(channel_id=ctx.channel_id):
        await ctx.respond("進行中のゲームがあります。先にそちらを終了して下さい。")
        return
    word_count = int(word_count)
    game = GameInfo(channel_id=ctx.channel_id, word_count=word_count)
    games_func.save_game(game)
    view = discord.ui.View(timeout=None)
    view.add_item(button_classes.GameJoinButton())
    view.add_item(button_classes.GameLeaveButton())
    view.add_item(button_classes.GameStartButton())
    view.add_item(button_classes.GameQuitButton())

    embed = discord.Embed(title="参加する人は参加ボタンを押して下さい。\n用意が出来たらスタートボタンでゲームを開始できます。\n\n中止ボタンでゲームを中止出来ます。",
                          color=discord.Color.blue())

    await ctx.respond(embed=embed, view=view)


@bot.event
async def on_message(message: discord.Message):
    if not games_func.is_game_exists(channel_id=message.channel.id):
        return
    if message.author.bot:
        return  # ボットは無視
    # 答え合わせの処理
    game: GameInfo = games_func.get_game(channel_id=message.channel.id)
    if not game.is_answering(user_id=message.author.id):
        return
    is_correct, elapsed_time = game.submit_answer(user_id=message.author.id, user_answer=message.content)
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

        if game.is_all_player_answered():
            if is_last_question:
                embed = generate_all_aggregate_embed(game, message.guild)
                await message.channel.send(embed=embed)
                return
            # 次の問題へ
            view = discord.ui.View(timeout=None)
            view.add_item(button_classes.GameQuitButton())
            embed = discord.Embed(title="全員が答え合わせを終了しました。\n2秒後に次の問題に進みます。", description="中止ボタンでゲームを中止出来ます。")
            await message.channel.send(embed=embed, view=view)
            await asyncio.sleep(2)
            q_kanji = game.get_next_question()
            q_number = game.question_index + 1
            embed = discord.Embed(title=f"問題{q_number}：{q_kanji}", color=discord.Color.green())
            for user_id in game.player_list:
                game.start_answering(user_id=user_id)
            game.save()
            view = discord.ui.View(timeout=None)
            view.add_item(button_classes.NextQuestionButton())
            view.add_item(button_classes.GameQuitButton())
            await message.channel.send(embed=embed, view=view)


def generate_all_aggregate_embed(game: GameInfo, guild: discord.Guild):
    embed = discord.Embed(title="全員の平均タイム", color=discord.Color.orange())
    players_sorted_time, players_not_answered_count = game.aggregate_all_result()
    ranking = 0
    print(players_sorted_time)
    for t in players_sorted_time:
        user_id = t[0]
        average_time = t[1]
        ranking += 1
        user = guild.get_member(user_id)
        embed.add_field(name=f"{ranking}位 {user.name}",
                        value=f"{average_time:.03f}秒\n未回答の問題：{players_not_answered_count[user_id]}問",
                        inline=False)
    return embed


bot.run(envs.TOKEN)
