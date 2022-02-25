from classes.game_info import GameInfo

games = {}


def get_game(channel_id: int):
    return games.get(channel_id)


def save_game(game: GameInfo):
    channel_id = game.channel_id
    games[channel_id] = game


def remove_game(game: GameInfo):
    channel_id = game.channel_id
    games.pop(channel_id, None)


def is_game_exists(channel_id: int):
    if channel_id in games:
        return True
    else:
        return False
