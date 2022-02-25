import json
import random

with open('susida.json', encoding='utf-8') as f:
    sushida_dict = json.load(f)


class GameInfo:
    def __init__(self, channel_id: int, word_count: int):
        self.competitor_time_list = {}
        self.competitor_status = {}
        self.start_time = int()
        self.player_list = []
        self.channel_id = channel_id
        self.question_list = generate_question_list(word_count)
        self.question_index_num = 0
        self.word_count = word_count

    def add_player(self, member_id: int):
        self.player_list.append(member_id)
        self.competitor_time_list[member_id] = []
        self.competitor_status[member_id] = 'answering'

    def remove_player(self, member_id: int):
        self.player_list.remove(member_id)
        del self.competitor_time_list[member_id]
        del self.competitor_status[member_id]

    def next_question(self):
        pass

    def end_game(self):
        pass


def generate_question_list(word_count: int):
    question_lists = random.sample(sushida_dict[str(word_count)], 10)
    return question_lists
