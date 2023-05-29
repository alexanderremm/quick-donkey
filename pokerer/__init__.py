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
from .game_manager import GameManager
from .message import Message
from .player import Player

# Third-party includes
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, emit, SocketIO

# Standard includes
import os

# Global list of games
GM = GameManager()

def create_app(test_config=None):
    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'pokerer.sqlite')
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    try:
    # Ensure the instance folder exists
        os.makedirs(app.instance_path)
    except OSError:
        pass

    socketio = SocketIO(app)

    @app.route("/", methods=["POST", "GET"])
    def home():
        session.clear()
        if request.method == "POST":
            name = request.form.get("name")
            code = request.form.get("code").upper()
            join = request.form.get("join", False)
            create = request.form.get("create", False)

            # Ensure the user has entered their name
            if not name:
                return render_template("home.html", error="Please enter a name.", code=code, name=name)
            
            # Ensure the user has entered a game code
            if join != False and not code:
                return render_template("home.html", error="Please enter a game code.", code=code, name=name)
            
            # Attempt to create a game
            game = code
            if create != False:
                game = GM.create_new_game()
            # The game code entered does not exist
            elif code not in GM.get_list_of_game_codes():
                return render_template("home.html", error="The game does not exist.", code=code, name=name)
            
            # Check that the username selected is not already in use
            names_list = GM.get_list_of_player_names_in_game(game)
            for _ in range(len(names_list)):
                if name.strip() in names_list:
                    return render_template("home.html", error="The name you have chosen is already taken. Please use a different name.", code=code, name=name)

            # Join the game
            session["game"] = game
            session["name"] = name

            return redirect(url_for("game"))

        return render_template("home.html")
    
    @app.route("/game")
    def game():
        game = session.get("game")
        # Make sure we can only get to the game page if we are a valid user
        if game is None or session.get("name") is None or not GM.valid_game(game):
            return redirect(url_for("home"))

        return render_template("game.html", game=game, messages=GM.convert_game_messages_to_json(game))
    
    @socketio.on("message")
    def message(data):
        game = session.get("game")
        # Make sure the game exists
        if not GM.valid_game(game):
            return

        msg = Message(session.get("name"), data["data"])
        
        send(msg.to_json(), to=game)
        GM.add_message_to_game(game, msg)
        print(f"{session.get('name')} said: {data['data']}\n")
    
    @socketio.on("connect")
    def connect(auth):
        game = session.get("game")
        name = session.get("name")

        # Make sure we can only join the game if it's a valid game
        if not game or not name:
            return
        if not GM.valid_game(game):
            leave_room()
            return
        
        # Join the game
        join_room(game)
        player = Player(name)
        GM.add_player_to_game(game, player)
        msg = Message(name, "has entered the game")
        GM.add_message_to_game(game, msg)
        send(msg.to_json(), to=game)
        print(f"{name} joined game {game}\n")

        # Update player list on clients
        emit("update_players", GM.convert_game_players_list_to_json(game), to=game)

    @socketio.on("disconnect")
    def disconnect():
        game = session.get("game")
        name = session.get("name")
        # Leave the game
        leave_room(game)

        # Update our global games list
        if GM.valid_game(game):
            GM.remove_player_from_game(game, name)

        # Log the event
        msg = Message(name, "has left the game")
        GM.add_message_to_game(game, msg)
        send(msg.to_json(), to=game)
        print(f"{name} left game {game}\n")

        # Update player list on clients
        emit("update_players", GM.convert_game_players_list_to_json(game), to=game)

    @socketio.on("ready_update")
    def ready_update(data):
        game = session.get("game")
        name = session.get("name")

        # Make sure the game exists
        if not GM.valid_game(game):
            return
        
        # Update player's ready status
        is_ready = data["is_ready"]
        vote = data["vote"]
        GM.update_player_info(game, name, is_ready, vote)
        if is_ready:
            msg = Message(name, "is ready!")
            print(f"{name} is ready!\n")
        else:
            msg = Message(name, "is not ready.")
            print(f"{name} is not ready.\n")
        
        # Log the event
        GM.add_message_to_game(game, msg)
        send(msg.to_json(), to=game)

        # Update player list on clients
        emit("update_players", GM.convert_game_players_list_to_json(game), to=game)
    
    return app, socketio