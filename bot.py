import discord
import random
from datetime import datetime, timedelta, timezone
import json
import numpy
import asyncio

import settings

TOKEN = settings.TOKEN
client = discord.Client(intents=discord.Intents.all())
jst = timezone(timedelta(hours=9), 'JST')
dt_now = datetime.now(jst)
count_active = []
time_dic = {}
q_num_dic = {}
with open('susida.json', encoding='utf-8') as f:
    sushida_dict = json.load(f)
competitor_time = {}
competitor_status = {}
question_num_dict = {}
start_time_dict = {}
random_question = {}
level_dict = {}
ranking_file_path = '/home/alpaca-data/typing-data/global-ranking.json'
with open(ranking_file_path) as f:
    global_ranking_dict: dict = json.load(f)


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="「!ヘルプ」でヘルプ", type=1))
    print('ready')


@client.event
async def on_message(message):
    global count_active
    if message.author.bot:
        return
    if message.guild is None:
        await dm_commands(message)
    # ヘルプをembedで送信
    elif message.content in {'!ヘルプ', '！ヘルプ'}:
        await help_message(message=message)
    elif message.content in {'!global', '!グローバル', '！グローバル'}:
        await send_global_ranking(message=message)
    elif message.content in {'!招待', '！招待'}:
        await message.channel.send(
            'https://discord.com/api/oauth2/authorize?client_id=736243567931949136&permissions=347200&scope=bot')
    elif message.content == '！タイピング' or message.content == '!タイピング':
        await game_start(message=message)
    elif message.content == '終了':
        await end_game(message=message)

    elif message.content == '次':
        await next_question(message)

    elif message.channel.id in competitor_time:
        await answering(message)


async def game_start(message):
    embed = discord.Embed(title='レベルを選択して下さい', description='レベルの番号を送って下さい。',
                          color=0x85cc00)
    val = 0
    while val < 15:
        val = val + 1
        if val == 13:
            embed.add_field(name='［13］14文字以上', value='最高難易度の14文字以上の問題です。', inline=False)
            break
        embed.add_field(name='［' + str(val) + '］' + str(val + 1) + '文字', value=str(val + 1) + '文字の問題です。',
                        inline=False)
    wizzard = await message.channel.send(embed=embed)
    competitor_time[message.channel.id] = {}

    def reaction_check(reaction, user):
        if reaction.message.id == wizzard.id:
            if not user.bot:
                if str(reaction) in {'➡', '<:sanka:749562970345832469>'}:
                    return True
        return False

    def bot_check(m):
        return m.channel == message.channel and m.author == message.author \
               and m.author.bot != True

    level_select = await client.wait_for('message', check=bot_check)
    try:
        level = int(level_select.content) + 1
    except ValueError:
        embed = discord.Embed(title='エラー：キャンセルしました',
                              description='レベルの番号以外が入力されました。\n半角数字で、レベルの番号を入力して下さい。', color=discord.Color.red())
        await wizzard.edit(embed=embed)
        return
    if str(level) not in sushida_dict:
        embed = discord.Embed(title='エラー：キャンセルしました',
                              description='レベルの番号以外が入力されました。\n半角数字で、レベルの番号を入力して下さい。', color=discord.Color.red())
        await wizzard.edit(embed=embed)
        return
    question_num = 0
    question_num_dict[message.channel.id] = question_num
    random_question[message.channel.id] = random.sample(sushida_dict[str(level)], 10)
    level_dict[message.channel.id] = level
    embed = discord.Embed(title='参加する人はリアクションを押して下さい。',
                          description='参加する人は<:sanka:749562970345832469>のリアクションを押して下さい。\n➡のリアクションで募集を締め切ります。')
    await wizzard.edit(embed=embed)
    await wizzard.add_reaction('<:sanka:749562970345832469>')
    await wizzard.add_reaction('➡')
    level_loop = True
    while level_loop is True:
        reaction, user = await client.wait_for('reaction_add', check=reaction_check)
        if str(reaction) == '➡':
            if len(competitor_time[message.channel.id]) == 0:
                await message.channel.send('参加リアクションが押されていないため、ゲームを開始できません。')
            break
        if user.id in competitor_time[message.channel.id]:
            continue
        if user.id in competitor_status:
            await message.channel.send(f'{user.mention} 既に他のチャンネル/サーバーでゲームに参加しています。')
            continue
        competitor_time[message.channel.id][user.id] = []
        competitor_status[user.id] = 'answering'
        continue
    await wizzard.remove_reaction(emoji='➡', member=client.get_user(736243567931949136))
    await wizzard.remove_reaction(emoji='<:sanka:749562970345832469>', member=client.get_user(736243567931949136))
    embed = discord.Embed(title='第' + str(question_num + 1) + '問',
                          description=random_question[message.channel.id][question_num][1])
    msg = await message.channel.send(embed=embed)
    start_time_dict[message.channel.id] = msg.created_at.timestamp()
    return


async def end_game(message):
    if message.channel.id not in competitor_time:
        await message.channel.send('このチャンネルで進行中のゲームはありません。')
        return
    if message.author.id not in competitor_time[message.channel.id]:
        await message.channel.send('あなたはこのチャンネルで進行中のゲームに参加していません。')
        return
    embed2 = generate_ranking_embed(message)
    await message.channel.send(embed=embed2)
    del random_question[message.channel.id]
    for user in competitor_time[message.channel.id]:
        del competitor_status[user]
    del competitor_time[message.channel.id]
    del question_num_dict[message.channel.id]
    del start_time_dict[message.channel.id]
    await message.channel.send('現在進行中のゲームを終了しました。')
    return


async def send_global_ranking(message):
    embed = discord.Embed(title='グローバルランキング(上位10位)',
                          description='このBotが導入されている全サーバーでのランキングです。'
                                      '\n※ランキングに載るには、レベル10で全問題に回答する必要があります。'
                                      '\n100位までのランキングを表示するには、60秒以内に⏩のリアクションをして下さい。',
                          color=discord.Color.dark_magenta())
    global_ranking = global_ranking_sort()
    for list_top in global_ranking:
        if global_ranking.index(list_top) == 11:
            break
        player_name = client.get_user(int(list_top[0])).name
        player_time = list_top[1]
        embed.add_field(name='［' + str(global_ranking.index(list_top) + 1) + '位］' + player_name + 'さん',
                        value='平均タイム：' + f'{player_time:.3f}' + '秒',
                        inline=False)
        continue
    ranking_msg = await message.channel.send(embed=embed)
    await ranking_msg.add_reaction('⏩')

    def reaction_check(reaction, user):
        if reaction.message.id == ranking_msg.id:
            if not user.bot:
                if str(reaction) == '⏩':
                    return True
        return False

    try:
        reaction, user = await client.wait_for('reaction_add', check=reaction_check, timeout=60)
    except asyncio.TimeoutError:
        await ranking_msg.remove_reaction(emoji='⏩', member=client.get_user(736243567931949136))
        return
    else:
        embed = discord.Embed(title='グローバルランキング(上位100位)',
                              description='このBotが導入されている全サーバーでのランキングです。'
                                          '\n※ランキングに載るには、レベル10で全問題に回答する必要があります。',
                              color=discord.Color.dark_magenta())
        for list_top in global_ranking:
            if global_ranking.index(list_top) == 101:
                break
            player_name = client.get_user(int(list_top[0])).name
            player_time = list_top[1]
            embed.add_field(name='［' + str(global_ranking.index(list_top) + 1) + '位］' + player_name + 'さん',
                            value='平均タイム：' + f'{player_time:.3f}' + '秒',
                            inline=False)
            continue
        await ranking_msg.edit(embed=embed)
    return


async def next_question(message):
    if message.channel.id in competitor_time:
        if message.author.id in competitor_time[message.channel.id]:
            question_num = question_num_dict[message.channel.id]
            question_num = question_num + 1
            question_num_dict[message.channel.id] = question_num
            for user in competitor_time[message.channel.id]:
                competitor_status[user] = 'answering'
            if len(random_question[message.channel.id]) - 1 == question_num:
                embed = discord.Embed(title='最終問題です！第' + str(question_num + 1) + '問',
                                      description=random_question[message.channel.id][question_num][1])
            else:
                embed = discord.Embed(title='第' + str(question_num + 1) + '問',
                                      description=random_question[message.channel.id][question_num][1])
            msg = await message.channel.send(embed=embed)
            start_time_dict[message.channel.id] = msg.created_at.timestamp()
            question_num_dict[message.channel.id] = question_num


async def answering(message):
    if message.author.id in competitor_time[message.channel.id]:
        if competitor_status[message.author.id] == 'answering':
            question_num = question_num_dict[message.channel.id]
            if message.content == random_question[message.channel.id][question_num][0]:
                answer_end = message.created_at.timestamp()
                answer_start = start_time_dict[message.channel.id]
                embed = discord.Embed(title='正解です！',
                                      description='解答時間：' + str(answer_end - answer_start) + '秒')
                await message.channel.send(message.author.mention, embed=embed)
                if len(random_question[message.channel.id]) - 1 == question_num:
                    competitor_status[message.author.id] = 'ended'
                else:
                    competitor_status[message.author.id] = 'answered'
                competitor_time[message.channel.id][message.author.id].append(answer_end - answer_start)
                finished_user_count = 0
                for user in competitor_time[message.channel.id]:
                    if competitor_status[user] == 'ended':
                        finished_user_count = finished_user_count + 1
                if len(random_question[message.channel.id]) - 1 == question_num:
                    competitor_status[message.author.id] = 'ended'
                    embed2 = discord.Embed(title='平均タイム',
                                           description='あなたの平均タイムです', color=discord.Color.dark_teal())
                    name = message.author.name
                    average = numpy.average(competitor_time[message.channel.id][message.author.id])
                    if len(competitor_time[message.channel.id][message.author.id]) != len(
                            random_question[message.channel.id]):
                        global_save = False
                        not_answered = str(
                            len(random_question[message.channel.id]) - len(
                                competitor_time[message.channel.id][message.author.id])) + '問'
                    else:
                        not_answered = 'なし'
                        if level_dict[message.channel.id] == 10:
                            global_save = True
                        else:
                            global_save = False
                    embed2.add_field(name=name + 'さん',
                                     value='平均タイム：' + f'{average:.3f}' + '秒\n未回答の問題：' + not_answered)
                    await message.channel.send(embed=embed2)
                    if global_save is True:
                        global_ranking_add(player_id=message.author.id, score=average)
                if finished_user_count == len(competitor_time[message.channel.id]):
                    embed2 = generate_ranking_embed(message)
                    del random_question[message.channel.id]
                    for user in competitor_time[message.channel.id]:
                        del competitor_status[user]
                    del competitor_time[message.channel.id]
                    del question_num_dict[message.channel.id]
                    del start_time_dict[message.channel.id]
                    del level_dict[message.channel.id]
                    await message.channel.send('ゲームが終了しました', embed=embed2)
                return
            else:
                embed = discord.Embed(title='不正解です！',
                                      description='もう一度お試し下さい。')
                await message.channel.send(message.author.mention, embed=embed)
                return


async def help_message(message):
    embed = discord.Embed(title="ヘルプ・コマンド一覧", description="こんな感じ\n問「新入生歓迎会」：解「しんにゅうせいかんげいかい」", color=0x0008ff)
    embed.add_field(name='!タイピング',
                    value="・レベルを選択し、ゲームを開始します。\nランダムに10問出題されます。", inline=False)
    embed.add_field(name='次',
                    value="・次の問題を出します。\n(進行中のゲームがない場合には反応しません。)", inline=False)
    embed.add_field(name='終了 or 終わり',
                    value="・現在進行中のゲームを終了させます。", inline=False)
    await message.channel.send(embed=embed)
    return


async def dm_commands(message):
    if message.content == 'サーバー':
        await message.channel.send(str(len(client.guilds)))
        return


def global_ranking_add(player_id, score):
    global_ranking_dict[str(player_id)] = score
    with open(ranking_file_path, 'w') as e:
        json.dump(global_ranking_dict, e, indent=4)
    return


def global_ranking_sort():
    global_ranking = sorted(global_ranking_dict.items(), key=lambda x: x[1])
    return global_ranking


def generate_ranking_embed(message):
    embed = discord.Embed(title='平均タイム',
                          description='参加者の平均タイムです', color=discord.Color.red())
    competitor_average_time = {}
    for player in competitor_time[message.channel.id]:
        average = numpy.average(competitor_time[message.channel.id][player])
        competitor_average_time[player] = average
    competitor_ranking = sorted(competitor_average_time.items(), key=lambda x: x[1])
    for val in competitor_ranking:
        player_id = val[0]
        player_time = val[1]
        rank = competitor_ranking.index(val) + 1
        name = client.get_user(player_id).name
        if len(competitor_time[message.channel.id][player_id]) != len(
                random_question[message.channel.id]):
            not_answered = str(
                len(random_question[message.channel.id]) - len(
                    competitor_time[message.channel.id][player_id])) + '問'
        else:
            not_answered = 'なし'
        embed.add_field(name='［' + str(rank) + '位］' + name + 'さん',
                        value='平均タイム：' + f'{player_time:.3f}' + '秒\n未回答の問題：' + not_answered,
                        inline=False)
    return embed


def generate_average_embed(message):
    pass


client.run(TOKEN)
