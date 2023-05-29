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

class Game:
    def __init__(self, code):
        """Data class to represent a scrum poker game."""
        self.code = code
        self.num_members = 0
        self.members = []
        self.messages = []

    def convert_players_list_to_json(self):
        tmp = []
        for member in self.members:
            tmp.append(member.to_json())

        return tmp
    
    def convert_messages_list_to_json(self):
        tmp = []
        for msg in self.messages:
            tmp.append(msg.to_json())
        
        return tmp
    
    def get_player_by_name(self, name):
        for member in self.members:
            if name == member.name:
                return member
