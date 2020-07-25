import discord
import re
import os
import time
import asyncio
from datetime import datetime, timedelta, timezone

'''
変数説明
count_activeリスト･･･入力時間をcountしているユーザーのリスト
time_dic･･･キー：ユーザーID 値：入力開始時のunix時間
q_num_dic･･･サーバーごとの問題番号の辞書
困ってるんで変数名で提案があったらよろしく！
'''

TOKEN = os.environ['DISCORD_BOT_TOKEN']
client = discord.Client()
jst = timezone(timedelta(hours=9), 'JST')
dt_now = datetime.now(jst)
count_active = []
time_dic = {}
q_num_dic = {}
answer_list = ['しかくいたたみをまるくはく', 'ゆうこうきげんがきれました', 'とくしょうははわいりょこう', 'さんかくかんすうがもんだい', 'ていきあつがはったつちゅう', 'ゆうきゅうきゅうかをつかう',
               'とっぴんぐはちょこれーとで',
               'みでぃあむでやいてください', 'うぃすきーをおんざろっくで', 'ひやしちゅうかはじめました', 'おれのけーきくったのだれだ',
               'そんなこわいかおするなって', 'かようびはていきゅうびです', 'つかいすてこんたくとれんず', 'だれもはんのうしてくれない']

question_list = ['四角い畳を丸く掃く', '有効期限が切れました', '特賞はハワイ旅行', '三角関数が問題', '低気圧が発達中', '有給休暇を使う', 'トッピングはチョコレートで',
                 'ミディアムで焼いてください', 'ウィスキーをオンザロックで', '冷やし中華始めました', '俺のケーキ食ったの誰だ',
                 'そんな恐い顔するなって', '火曜日は定休日です', '使い捨てコンタクトレンズ', '誰も反応してくれない']


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
        embed.add_field(name='タイピング問題',
                        value="・タイピング1\n・レベル2以降は実装予定…", inline=False)
        embed.add_field(name='次',
                        value="・次の問題を出します。", inline=False)
        embed.add_field(name='終了 or 終わり',
                        value="・現在進行中のゲームを終了させます。", inline=False)
        await message.channel.send(embed=embed)

    # ゲーム終了
    if message.content == '終わり' or message.content == '終了':
        # ゲームが実行中じゃなかった場合
        if message.guild.id not in q_num_dic:
            await message.channel.send('現在進行中のゲームはありません。')
            return
        # 実行中だった場合。関数化予定
        del q_num_dic[message.guild.id]
        # サーバーメンバー全員をfor in で回す
        for i in message.guild.members:
            # カウントがactiveの場合、deactiveに()
            if i.id in count_active:
                count_active.remove(i.id)
            # 入力開始したけど終了していない場合に、入力開始時の時刻を削除
            if i.id in time_dic:
                del time_dic[i.id]
            continue
        await message.channel.send('現在進行中のゲームを終了しました。')
        return

    # 次の問題
    # 今ゲームが進行中かどうかのチェック
    if message.guild.id in q_num_dic:
        if message.content == '次':
            # 関数化予定
            # インデックスを取得
            q_num = q_num_dic.get(message.guild.id)
            # インデックスに1を足す(前回の問題から1進める)
            q_num = q_num + 1
            # メッセージを送信。(インデックスに1足して問題番号にしてるのは、インデックスは0から始まるから)
            await message.channel.send('第' + str(q_num + 1) + '問\n' + '問題：' + question_list[q_num])
            # countをactiveに()
            count_active.append(message.author.id)
            # 問題番号を上書き
            q_num_dic[message.guild.id] = q_num
            return

    # タイピング練習開始
    if message.content == 'タイピング1':
        # ゲームが既に進行中の場合
        if message.guild.id in q_num_dic:
            await message.channel.send('現在ゲームが進行中です。')
            return
        # 最初なのでインデックスは0
        q_num = 0
        # 関数化予定
        await message.channel.send(
            'レベル1\n13文字のタイピング練習です。15問あります。10秒後に開始します。\n**※全部ひらがなの為、IMEの学習機能を無効にされることを強くお勧めします。**')
        await asyncio.sleep(10)
        await message.channel.send('第1問\n' + question_list[q_num])
        for i in message.guild.members:
            count_active.append(i.id)
        q_num_dic[message.guild.id] = q_num
        return

    # 解答チェック
    if message.author.id in count_active:
        q_num = q_num_dic.get(message.guild.id)
        print(answer_list[q_num])
        # 間違っていた場合
        if message.content != answer_list[q_num]:
            await message.channel.send('答えが間違っています。')
            return
        # 正解の場合
        print(q_num)
        # 経過時間の計算
        end = time.time()
        start = time_dic[message.author.id]
        elapse = end - start + 1
        # start時間の削除(リセット)
        del time_dic[message.author.id]
        # countをdeactiveに()
        count_active.remove(message.author.id)
        await message.channel.send(message.author.mention + '経過時間：' + str(elapse) + '秒')
        # 最終問題の場合(インデックスが14の場合)
        if q_num == 14:
            # 終了時の処理そのまま。関数化予定
            del q_num_dic[message.guild.id]
            for i in message.guild.members:
                if i.id in count_active:
                    print('in')
                    count_active.remove(i.id)
                if i.id in time_dic:
                    del time_dic[i.id]
                continue
            await message.channel.send('以上で問題は終了です。')
        return


# 入力検知
@client.event
async def on_typing(channel, user, when):
    # ユーザーのcountがactiveかどうか確認
    if user.id in count_active:
        start = time.time()
        time_dic[user.id] = start


client.run(TOKEN)
