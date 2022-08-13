from utils.kv_namespaces import global_ranking_namespace


class GuildRanking:
    def __init__(self, guild_id: int, word_count: int, competitors_record: dict = None):
        self.guild_id = guild_id
        self.word_count = word_count
        if competitors_record is None:
            self.competitors_record = {}
        else:
            self.competitors_record = competitors_record

    def add_record(self, user_id: int, time: float):
        if user_id in self.competitors_record:
            # 過去の記録の方が早い場合は更新しない
            if self.competitors_record[user_id] < time:
                return
        self.competitors_record[user_id] = time

    def get_all_records(self, sort_by_time: bool = True):
        records = {}
        if sort_by_time:
            sorted_tuple = sorted(self.competitors_record.items(), key=lambda x: x[1])
            i: tuple
            for i in sorted_tuple:
                user_id = i[0]
                time = self.competitors_record[user_id]
                records[user_id] = time
        else:
            for user_id in self.competitors_record:
                records[user_id] = self.competitors_record[user_id]
        return records

    def is_user_in_ranking(self, user_id: int):
        return user_id in self.competitors_record

    def get_user_record(self, user_id: int):
        return self.competitors_record.get(user_id)


class GlobalRanking:
    def __init__(self, word_count: int, competitors_record: dict):
        self.word_count = word_count
        self.competitors_records = {}
        for user_id in competitors_record:
            self.competitors_records[int(user_id)] = competitors_record[user_id]

    def is_user_in_ranking(self, user_id: int):
        return int(user_id) in self.competitors_records

    def get_user_record(self, user_id: int):
        return self.competitors_records.get(user_id)

    async def add_record(self, user_id: int, time: float):
        if user_id in self.competitors_records:
            # 過去の記録の方が早い場合は更新しない
            if self.competitors_records[user_id] < time:
                return
        self.competitors_records[user_id] = time
        await global_ranking_namespace.write({user_id: time})

    def get_all_records(self, sort_by_time: bool = True):
        records = {}
        if sort_by_time:
            sorted_tuple = sorted(self.competitors_records.items(), key=lambda x: x[1])
            i: tuple
            for i in sorted_tuple:
                user_id = i[0]
                time = self.competitors_records[user_id]
                records[user_id] = time
        else:
            for user_id in self.competitors_records:
                records[user_id] = self.competitors_records[user_id]
        return records