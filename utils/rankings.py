from classes.ranking_class import GlobalRanking, GuildRanking
from utils.kv_namespaces import *

# 将来的には可変に？
RANKING_WORD_COUNT = 10


async def get_guild_ranking(guild_id: int) -> GuildRanking:
    data = await guild_ranking_namespace.read(str(guild_id))
    return GuildRanking(json_data=data)


async def add_guild_ranking_records(game) -> None:
    guild_ranking = await get_guild_ranking(game.guild_id)
    if guild_ranking is None:
        guild_ranking = GuildRanking(word_count=RANKING_WORD_COUNT, guild_id=game.guild_id)
    guild_ranking.add_records(game.players_average_time)
    await guild_ranking_namespace.write({game.guild_id: guild_ranking.json()})
    return


async def get_global_ranking() -> GlobalRanking:
    kv_keys = await global_ranking_namespace.list_keys()
    data = {}
    for user_id in kv_keys:
        data[int(user_id)] = float(await global_ranking_namespace.read(user_id))
    return GlobalRanking(word_count=RANKING_WORD_COUNT, competitors_record=data)


async def add_global_ranking_records(user_records: dict) -> None:
    global_ranking_user_ids = await global_ranking_namespace.list_keys()
    formatted_records = user_records
    for user_id in user_records:
        time = user_records[user_id]
        if str(user_id) in global_ranking_user_ids:
            # 過去の記録の方が早い場合は更新しない
            if float(await global_ranking_namespace.read(str(user_id))) < time:
                formatted_records.pop(user_id)
    await global_ranking_namespace.write(formatted_records)
    return None
