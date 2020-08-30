import discord
import os
import time
import asyncio
from datetime import datetime, timedelta, timezone
import json

TOKEN = os.environ['DISCORD_BOT_TOKEN']
client = discord.Client()
jst = timezone(timedelta(hours=9), 'JST')
dt_now = datetime.now(jst)
count_active = []
time_dic = {}
q_num_dic = {}
with open('susida.json', encoding='utf-8') as f:
    susida_dict = json.load(f)
level_dict = {}
competitor_time = {}
competitor_status = {}
question_num_dict = {}
start_time_dict = {}


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(name="「ヘルプ」でヘルプ", type=1))
    print('ready')


@client.event
async def on_message(message):
    global count_active
    if message.author.bot:
        return
    # ヘルプをembedで送信
    if message.content == 'ヘルプ':
        embed = discord.Embed(title="ヘルプ・コマンド一覧", description="こんな感じ\n問「新入生歓迎会」：解「しんにゅうせいかんげいかい」", color=0x0008ff)
        embed.add_field(name='タイピング',
                        value="・レベルを選択し、ゲームを開始します。", inline=False)
        embed.add_field(name='次',
                        value="・次の問題を出します。", inline=False)
        embed.add_field(name='終了 or 終わり',
                        value="・現在進行中のゲームを終了させます。", inline=False)
        await message.channel.send(embed=embed)

    elif message.content == 'タイピング':
        embed = discord.Embed(title='レベルを選択して下さい', description='レベルの番号を送って下さい。',
                              color=0x85cc00)
        val = 0
        while val < 15:
            val = val + 1
            if val == 14:
                embed.add_field(name='［13］14文字以上', value='最高難易度の14文字以上の問題です。', inline=False)
                break
            embed.add_field(name='［' + str(val) + '］' + str(val + 1) + '文字', value=str(val + 1) + '文字の問題です。',
                            inline=False)
        wizzard = await message.channel.send(embed=embed)
        competitor_time[message.channel.id] = {}

        def not_bot(user):
            if user.bot:
                return False
            else:
                return True

        def reaction_check(reaction, user):
            if reaction.message.id == wizzard.id:
                if not user.bot:
                    if str(reaction) == '➡' or str(reaction) == '<:sanka:749562970345832469>':
                        return True
            return False

        def bot_check(m):
            return m.channel == message.channel and m.author == message.author and m.author.bot != True

        level_select = await client.wait_for('message', check=bot_check)
        try:
            level = int(level_select.content)+1
        except ValueError:
            embed = discord.Embed(title='エラー：キャンセルしました',
                                  description='レベルの番号以外が入力されました。\n半角数字で、レベルの番号を入力して下さい。', color=discord.Color.red())
            await wizzard.edit(embed=embed)
            return
        if str(level + 1) not in susida_dict:
            embed = discord.Embed(title='エラー：キャンセルしました',
                                  description='レベルの番号以外が入力されました。\n半角数字で、レベルの番号を入力して下さい。', color=discord.Color.red())
            await wizzard.edit(embed=embed)
            return
        question_num = 0
        question_num_dict[message.channel.id] = question_num
        level_dict[message.channel.id] = level
        embed = discord.Embed(title='参加する人はリアクションを押して下さい。',
                              description='参加する人は<:sanka:749562970345832469>のリアクションを押して下さい。\n➡のリアクションで募集を締め切ります。')
        await wizzard.edit(embed=embed)
        await wizzard.add_reaction('<:sanka:749562970345832469>')
        await wizzard.add_reaction('➡')
        level_loop = True
        while level_loop is True:
            print('reaction')
            reaction, user = await client.wait_for('reaction_add', check=reaction_check)
            if str(reaction) == '➡':
                break
            if user.id in competitor_time[message.channel.id]:
                continue
            if user.id in competitor_status:
                await message.channel.send('<@' + str(user.id) + '>既に他のチャンネル/サーバーでゲームに参加しています。')
                continue
            competitor_time[message.channel.id][user.id] = []
            competitor_status[user.id] = 'answering'
            continue
        await wizzard.remove_reaction(emoji='➡', member=client.get_user(539910964724891719))
        await wizzard.remove_reaction(emoji='<:sanka:749562970345832469>', member=client.get_user(539910964724891719))
        embed = discord.Embed(title='第' + str(question_num+1) + '問',
                              description=susida_dict[str(level)][question_num][1])
        start_time_dict[message.channel.id] = time.time()
        await message.channel.send(embed=embed)
        return

    elif message.content == '終了':
        if message.channel.id not in competitor_time:
            await message.channel.send('このチャンネルで進行中のゲームはありません。')
            return
        if message.author.id not in competitor_time[message.channel.id]:
            await message.channel.send('あなたはこのチャンネルで進行中のゲームに参加していません。')
            return
        del level_dict[message.channel.id]
        for user in competitor_time[message.channel.id]:
            del competitor_status[user]
        del competitor_time[message.channel.id]
        del question_num_dict[message.channel.id]
        del start_time_dict[message.channel.id]
        await message.channel.send('現在進行中のゲームを終了しました。')
        return

    elif message.content == '次':
        if message.channel.id in competitor_time:
            if message.author.id in competitor_time[message.channel.id]:
                question_num = question_num_dict[message.channel.id]
                level = level_dict[message.channel.id]
                question_num = question_num + 1
                question_num_dict[message.channel.id] = question_num
                for user in competitor_time[message.channel.id]:
                    competitor_status[user] = 'answering'
                embed = discord.Embed(title='第' + str(question_num+1) + '問',
                                      description=susida_dict[str(level)][question_num][1])
                start_time_dict[message.channel.id] = time.time()
                await message.channel.send(embed=embed)
                question_num_dict[message.channel.id] = question_num

    elif message.channel.id in competitor_time:
        if message.author.id in competitor_time[message.channel.id]:
            if competitor_status[message.author.id] == 'answering':
                question_num = question_num_dict[message.channel.id]
                level = level_dict[message.channel.id]
                if message.content == susida_dict[str(level)][question_num][0]:
                    answer_end = time.time()
                    answer_start = start_time_dict[message.channel.id]
                    await message.channel.send(message.author.mention)
                    embed = discord.Embed(title='正解です！',
                                          description='解答時間：' + str(answer_end - answer_start) + '秒')
                    await message.channel.send(embed=embed)
                    competitor_status[message.author.id] = 'answered'
                    competitor_time[message.channel.id][message.author.id].append(answer_end - answer_start)
                    return
                else:
                    embed = discord.Embed(title=message.author.mention + '不正解です！',
                                          description='もう一度お試し下さい。')
                    await message.channel.send(embed=embed)
                    return


client.run(TOKEN)
