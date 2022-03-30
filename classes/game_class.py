import games_func
import json
import random
import re
import time

import numpy as numpy

from google_input import FilterRuleTable, GoogleInput

with open('susida.json', encoding='utf-8') as f:
    sushida_dict = json.load(f)

table = FilterRuleTable.from_file("google_ime_default_roman_table.txt")
gi = GoogleInput(table)
alphabet_regex = re.compile('[ -~]+')


class GameObj:
    def __init__(self, channel_id: int, word_count: int):
        self.competitor_time = {}
        self.competitor_status = {}
        self.start_time = int()
        self.player_list = []
        self.channel_id = channel_id
        self.question_list = generate_question_list(word_count)
        self.question_index = -1
        self.word_count = word_count

    def save(self):
        games_func.save_game(self)

    def add_player(self, member_id: int):
        self.player_list.append(member_id)
        self.competitor_time[member_id] = []
        self.competitor_status[member_id] = 'answering'

    def remove_player(self, member_id: int):
        self.player_list.remove(member_id)
        del self.competitor_time[member_id]
        del self.competitor_status[member_id]

    def get_next_question(self):
        self.question_index += 1
        return self.question_list[self.question_index][1]

    def start_answering(self, user_id: int):
        self.start_time = time.time()
        self.competitor_status[user_id] = 'answering'

    def is_answering(self, user_id: int):
        return self.competitor_status[user_id] == 'answering'

    def is_all_player_answered(self):
        for status in self.competitor_status.values():
            if status != 'answered':
                return False
        return True

    def submit_answer(self, user_id: int, user_answer: str):
        """
        is_correctは正解の場合はTrue、不正解の場合はFalse
        Args:
            user_id:
            user_answer:

        Returns:
            is_correct: bool
            elapsed_time: int
        """
        is_answer_right = check_answer(self, user_answer)
        if is_answer_right:
            self.competitor_status[user_id] = 'answered'
            elapsed_time = time.time() - self.start_time
            self.competitor_time[user_id].append(elapsed_time)
            return True, elapsed_time
        return False, 0

    def aggregate_user_result(self, user_id: int):
        """
        回答したユーザーのみ集計する
        Args:
            user_id:

        Returns:
            average_time: float
        """
        average = numpy.average(self.competitor_time[user_id])
        not_answered_question_count = 10 - len(self.competitor_time[user_id])
        return average, not_answered_question_count

    def aggregate_all_result(self):
        """
        全員が回答したら、結果を集計する
        Returns:
            players_sorted_time: dict
            players_not_answered_question_count: dict
        """
        players_average_time = {}
        players_not_answered_question_count = {}
        for user_id in self.player_list:
            average = numpy.average(self.competitor_time[user_id])
            players_average_time[user_id] = average
            players_not_answered_question_count[user_id] = 10 - len(self.competitor_time[user_id])
        players_sorted_time = sorted(players_average_time.items(), key=lambda x: x[1])
        return players_sorted_time, players_not_answered_question_count


def generate_question_list(word_count: int):
    question_lists = random.sample(sushida_dict[str(word_count)], 10)
    return question_lists


def check_answer(game: GameObj, answer: str):
    if alphabet_regex.fullmatch(answer):
        answer = rome_to_hiragana(answer)
    answer = answer.replace('!', '！')
    answer = answer.replace('?', '？')
    question = game.question_list[game.question_index]
    right_answer = question[0]
    return right_answer == answer


def rome_to_hiragana(input_string):
    output = ""
    for c in input_string:
        result = gi.input(c)
        if result.fixed:
            output += result.fixed.output
        else:
            if not result.tmp_fixed and not result.next_candidates:
                output += result.input
    return output
