import json

from workers_kv.ext.async_workers_kv import Namespace


class GuildRanking:
    def __init__(self, guild_id: int, word_count: int, competitors_record: dict = None):
        self.guild_id = guild_id
        self.word_count = word_count
        if competitors_record is None:
            self.competitors_record = {}
        else:
            self.competitors_record = competitors_record

    def add_record(self, user_id: int, time: float):
        # KVに保存時JSONに変換するのでstr型に変換
        user_id = str(user_id)
        if user_id in self.competitors_record:
            # 過去の記録の方が早い場合は更新しない
            if self.competitors_record[user_id] < time:
                return
        self.competitors_record[user_id] = time

    def get_all_records(self, sort_by_time: bool = True):
        records = {}
        if sort_by_time:
            sorted_tuple = sorted(self.competitors_record.items(), key=lambda x: x[1])
            for i in sorted_tuple:
                user_id = int(i[0])
                time = i[1]
                records[user_id] = time
        else:
            for user_id in self.competitors_record:
                records[int(user_id)] = self.competitors_record[user_id]
        return records

    def is_user_in_ranking(self, user_id: int):
        return str(user_id) in self.competitors_record

    def get_user_record(self, user_id: int):
        return self.competitors_record.get(str(user_id))


class GlobalRankingNamespace:
    def __await__(self, namespace: Namespace):
        self.namespace = namespace
        self.cache = {}

    async def _init(self):
        self.cache = await self.fetch_all_records()

    def get_all_records(self):
        return self.cache

    async def fetch_all_records(self):
        data = {}
        for key in await self.namespace.list_keys():
            data[key] = float(await self.namespace.read(key))
        return data

    async def get_user_record(self, user_id: int):
        return self.cache.get(user_id)

    async def write_user_record(self, user_id: int, time: float):
        self.cache[user_id] = time
        await self.namespace.write({user_id: time})
        return None


class GuildsRankingNamespace:
    def __init__(self, namespace: Namespace):
        self.namespace = namespace
        self.cache = {}

    async def _init(self):
        self.cache = await self.fetch_all_records()

    def get_all_records(self):
        return self.cache

    async def fetch_all_records(self):
        data = {}
        for guild_id in await self.namespace.list_keys():
            guild_record_raw = await self.namespace.read(guild_id)
            guild_ranking = GuildRanking(guild_id=int(guild_id),
                                         word_count=int(guild_record_raw['word_count']),
                                         competitors_record=guild_record_raw['competitors_record'])
            data[int(guild_id)] = guild_ranking
        self.cache = data
        return data

    def get_guild_records(self, guild_id: int) -> GuildRanking:
        return self.cache.get(guild_id)

    async def write_record(self, guild_ranking: GuildRanking):
        guild_ranking_dict = guild_ranking.__dict__
        await self.namespace.write({guild_ranking_dict["guild_id"]: json.dumps(guild_ranking_dict)})
        return None
