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
from .utils import generate_timestamp

# Third-party includes
from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, emit, SocketIO

# Standard includes
import datetime
import os
import random
from string import ascii_uppercase

# Global list of games
GAMES = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in GAMES:
            break

    return code


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
                game = generate_unique_code(4)
                GAMES[game] = {"num_members": 0, "members": [], "messages": []}
            # The game code entered does not exist
            elif code not in GAMES:
                return render_template("home.html", error="The game does not exist.", code=code, name=name)
            
            # Check that the username selected is not already in use
            names_list = GAMES[game]["members"]
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
        if game is None or session.get("name") is None or game not in GAMES:
            return redirect(url_for("home"))

        return render_template("game.html", game=game, messages=GAMES[game]["messages"])
    
    @socketio.on("message")
    def message(data):
        game = session.get("game")
        # Make sure the game exists
        if game not in GAMES:
            return
        
        content = {
            "name": session.get("name"),
            "message": data["data"],
            "date": generate_timestamp()
        }
        send(content, to=game)
        GAMES[game]["messages"].append(content)
        print(f"{session.get('name')} said: {data['data']}")
    
    @socketio.on("connect")
    def connect(auth):
        game = session.get("game")
        name = session.get("name")

        # Make sure we can only join the game if it's a valid game
        if not game or not name:
            return
        if game not in GAMES:
            leave_room()
            return
        
        # Join the game
        join_room(game)

        # Log the event
        GAMES[game]["members"].append(name)
        GAMES[game]["num_members"] +=1
        content = { "name": name, "message": "has entered the game", "date": generate_timestamp() }
        GAMES[game]["messages"].append(content)
        send(content, to=game)
        print(f"{name} joined game {game}")

        # Update player list on clients
        emit("update_players", GAMES[game]["members"], to=game)

    @socketio.on("disconnect")
    def disconnect():
        game = session.get("game")
        name = session.get("name")
        # Leave the game
        leave_room(game)

        # Update our global games list
        if game in GAMES:
            GAMES[game]["members"].remove(name)
            GAMES[game]["num_members"] -= 1
            if GAMES[game]["num_members"] <= 0:
                del GAMES[game]

        # Log the event
        content = {"name": name, "message": "has left the game", "date": generate_timestamp()}
        GAMES[game]["messages"].append(content)
        send(content, to=game)
        print(f"{name} left game {game}")

        # Update player list on clients
        emit("update_players", GAMES[game]["members"], to=game)
    
    return app, socketio