from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# MongoDB client and database setup
client = MongoClient("mongodb://localhost:27017/")
db = client['user_database']
scores_collection = db['users']

@app.route("/")
def home():
    return render_template('game_portal.html')

@app.route("/select_difficulty", methods=['POST'])
def select_difficulty():
    name = request.form['name']
    age = request.form['age']
    difficulty = request.form['difficulty']
    
    # Check if the user already exists in the database
    existing_user = scores_collection.find_one({'name': name})
    
    if existing_user:
        # Redirect to the user profile page if user exists
        return redirect(url_for('user_profile', username=name))
    else:
        # Proceed to difficulty selection if new user
        return redirect(url_for(f"{difficulty}_games", name=name, age=age))

@app.route('/user_profile/<username>')
def user_profile(username):
    # Fetch all games played by the user
    user_games = list(scores_collection.find({'name': username}))
    
    # Calculate the average score
    total_score = sum(game['score'] for game in user_games)
    game_count = len(user_games)
    average_score_percentage = (total_score / (game_count * 100)) * 100 if game_count > 0 else 0

    # Format the game details for display
    formatted_games = format_scores(user_games)
    
    return render_template(
        'user_profile.html', 
        username=username, 
        games=formatted_games, 
        average_score=round(average_score_percentage, 2)
    )


@app.route("/easy_games/<name>/<age>")
def easy_games(name, age):
    return render_template('select_game.html', difficulty="easy", name=name, age=age, games=['tic_tac_toe', 'memory_game', 'rock_paper_scissors'])

@app.route("/moderate_games/<name>/<age>")
def moderate_games(name, age):
    return render_template('select_game.html', difficulty="moderate", name=name, age=age, games=['snake_game', 'red_square'])

@app.route("/hard_games/<name>/<age>")
def hard_games(name, age):
    return render_template('select_game.html', difficulty="hard", name=name, age=age, games=['breakout'])

@app.route("/game/<difficulty>/<game>/<name>/<age>")
def game(difficulty, game, name, age):
    template_mapping = {
        'tic_tac_toe': 'tic_tac_toe.html',
        'memory_game': 'memory_game.html',
        'rock_paper_scissors': 'rock_paper_scissors.html',
        'snake_game': 'snake_game.html',
        'red_square': 'red_square.html',
        'breakout': 'breakout.html'
    }
    template = template_mapping.get(game)
    if template:
        return render_template(template, name=name, age=age, difficulty=difficulty)
    else:
        return "Invalid game selection", 400

@app.route('/update_score', methods=['POST'])
def update_score():
    data = request.get_json()
    game_name = data.get('game')
    difficulty = data.get('difficulty')
    username = data.get('name')
    
    data['submitted_at'] = datetime.now()
    scores_collection.insert_one(data)

    # Redirect to the specific game's leaderboard with required parameters
    return jsonify(success=True), 200  # JSON response, as we're using fetch in JavaScript

@app.route('/dashboard/<difficulty>/<game>/scores/<username>')
def display_game_scores(difficulty, game, username):
    game_scores = scores_collection.find({
        'game': game
    }).sort('score', -1).limit(5)
    
    scores_list = format_scores(game_scores)
    
    return render_template('specific_game_scores.html', scores=scores_list, game=game, difficulty=difficulty, username=username)

def format_scores(results):
    scores_list = []
    for result in results:
        scores_list.append({
            'name': result.get('name', 'Unknown'),
            'age': result.get('age', 'Unknown'),
            'score': result.get('score', 0),
            'game': result.get('game', 'Unknown'),
            'submitted_at': result['submitted_at'].strftime('%Y-%m-%d %H:%M:%S')
        })
    return scores_list

@app.route('/debug/all_scores')
def debug_all_scores():
    all_scores = list(scores_collection.find())
    formatted_scores = format_scores(all_scores)
    return jsonify(formatted_scores)

if __name__ == "__main__":
    app.run(debug=True, port=5001)
