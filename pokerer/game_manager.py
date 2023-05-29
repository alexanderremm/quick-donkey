"""
 Copyright (c) 2023 Alexander Remm

 Permission is hereby granted, free of charge, to any person obtaining a copy of
 this software and associated documentation files (the "Software"), to deal in
 the Software without restriction, including without limitation the rights to
 use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
 the Software, and to permit persons to whom the Software is furnished to do so,
 subject to the following conditions:

 The above copyright notice and this permission notice shall be included in all
 copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
 FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
 COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
 IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
 CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
 """

# Project includes
from .game import Game

# Standard includes
import random
from string import ascii_uppercase

class GameManager:
    def __init__(self, len_of_codes=4):
        self.games = {}
        self.len_of_codes = len_of_codes

    def create_new_game(self):
        code = self.__generate_unique_code(self.len_of_codes)
        self.games[code] = Game(code)
        return code

    def delete_game(self, code):
        pass

    def get_list_of_game_codes(self):
        return [code for code in self.games.keys()]
    
    def get_list_of_player_names_in_game(self, code):
        return [player.name for player in self.games[code].members]
    
    def get_list_of_players_in_game(self, code):
        return [player for player in self.games[code].members]
    
    def valid_game(self, code):
        return code in self.get_list_of_game_codes()
    
    def convert_game_messages_to_json(self, code):
        game = self.games.get(code, None)
        if game is None:
            raise KeyError(f"No game exists for the following code: {code}")

        return game.convert_messages_list_to_json()
    
    def convert_game_players_list_to_json(self, code):
        game = self.games.get(code, None)
        if game is None:
            raise KeyError(f"No game exists for the following code: {code}")
        
        return game.convert_players_list_to_json()
    
    def add_message_to_game(self, code, msg):
        self.games[code].messages.append(msg)

    def add_player_to_game(self, code, player):
        self.games[code].members.append(player)
        self.games[code].num_members += 1

    def remove_player_from_game(self, code, name):
        if name not in self.get_list_of_player_names_in_game(code):
            raise KeyError(f"No user with the name {name} in game with code {code}")

        for idx, player in enumerate(self.games[code].members):
            if name == player.name:
                del self.games[code].members[idx]
        
        self.games[code].num_members -= 1
        if self.games[code].num_members <= 0:
            del self.games[code]

    def update_player_info(self, code, name, ready_status, vote):
        if name not in self.get_list_of_player_names_in_game(code):
            raise KeyError(f"No user with the name {name} in game with code {code}")
        
        player = self.games[code].get_player_by_name(name)
        player.ready = ready_status
        player.vote = vote


    def __generate_unique_code(self, length):
        while True:
            code = ""
            for _ in range(length):
                code += random.choice(ascii_uppercase)

            if code not in self.get_list_of_game_codes():
                break

        return code