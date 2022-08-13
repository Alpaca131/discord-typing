from classes.ranking_class import GlobalRanking, GuildRanking
from utils.kv_namespaces import *

# 将来的には可変に？
RANKING_WORD_COUNT = 10


async def get_guild_ranking(guild_id: int) -> GuildRanking:
    data = await guild_ranking_namespace.read(str(guild_id))
    return GuildRanking(guild_id=guild_id, word_count=RANKING_WORD_COUNT, competitors_record=data)


async def save_guild_ranking(guild_ranking: GuildRanking) -> None:
    await guild_ranking_namespace.write({guild_ranking.guild_id: guild_ranking.competitors_record})
    return None


async def get_global_ranking() -> GlobalRanking:
    kv_keys = await global_ranking_namespace.list_keys()
    data = {}
    for user_id in kv_keys:
        data[int(user_id)] = float(await global_ranking_namespace.read(user_id))
    return GlobalRanking(word_count=RANKING_WORD_COUNT, competitors_record=data)
