from flask import Flask, request, jsonify, render_template
import random

app = Flask(__name__)

# 1) Central Data Store: Dictionary (LEADERBOARD)
# Key: player name (str)
# Value: nested dict of cumulative stats
LEADERBOARD = {}

# Current match state (server-side)
CURRENT = {
    "p1": None,
    "p2": None,
    "p1_locked": False,  # after first game, winner is locked as p1
}

CHOICES = ["rock", "paper", "scissors"]

def ensure_player(name: str):
    if name not in LEADERBOARD:
        LEADERBOARD[name] = {
            "score": 0,
            "games_won": 0,
            "games_played": 0
        }

def round_winner(p1_choice, p2_choice):
    if p1_choice == p2_choice:
        return 0  # tie
    if (p1_choice == "rock" and p2_choice == "scissors") or \
       (p1_choice == "paper" and p2_choice == "rock") or \
       (p1_choice == "scissors" and p2_choice == "paper"):
        return 1  # p1 wins
    return 2      # p2 wins

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/start", methods=["POST"])
def api_start():
    data = request.get_json(force=True)
    p1 = (data.get("p1") or "").strip()
    p2 = (data.get("p2") or "").strip()

    if not p1 or not p2:
        return jsonify({"error": "Both player names are required."}), 400

    # Winner retention: if p1 is locked, user may not change it
    if CURRENT["p1_locked"] and p1 != CURRENT["p1"]:
        p1 = CURRENT["p1"]  # force retention

    # Register players in LEADERBOARD
    ensure_player(p1)
    ensure_player(p2)

    CURRENT["p1"] = p1
    CURRENT["p2"] = p2

    msg = f"Match started: {p1} vs {p2}. Click 'Play 10 Rounds'."
    return jsonify({"message": msg, "p1": p1, "p2": p2, "p1_locked": CURRENT["p1_locked"]})

@app.route("/api/play", methods=["POST"])
def api_play():
    p1 = CURRENT["p1"]
    p2 = CURRENT["p2"]
    if not p1 or not p2:
        return jsonify({"error": "Start a match first (enter Player 1 and Player 2)."}), 400

    # Game length: 10 rounds
    p1_round_wins = 0
    p2_round_wins = 0
    ties = 0
    rounds = []

    for i in range(10):
        c1 = random.choice(CHOICES)
        c2 = random.choice(CHOICES)
        w = round_winner(c1, c2)
        if w == 1:
            p1_round_wins += 1
        elif w == 2:
            p2_round_wins += 1
        else:
            ties += 1
        rounds.append({"round": i + 1, "p1_choice": c1, "p2_choice": c2, "winner": w})

    # Scoring: update cumulative stats in LEADERBOARD
    LEADERBOARD[p1]["score"] += p1_round_wins
    LEADERBOARD[p2]["score"] += p2_round_wins
    LEADERBOARD[p1]["games_played"] += 1
    LEADERBOARD[p2]["games_played"] += 1

    # Determine game winner (10-round game winner)
    if p1_round_wins > p2_round_wins:
        game_winner = p1
        LEADERBOARD[p1]["games_won"] += 1
    elif p2_round_wins > p1_round_wins:
        game_winner = p2
        LEADERBOARD[p2]["games_won"] += 1
    else:
        game_winner = p1  # tie-break: retain p1 (simple, deterministic)

    # Subsequent game flow: winner retained as Player 1
    CURRENT["p1"] = game_winner
    CURRENT["p2"] = None
    CURRENT["p1_locked"] = True

    return jsonify({
        "p1": p1,
        "p2": p2,
        "rounds_played": 10,
        "p1_round_wins": p1_round_wins,
        "p2_round_wins": p2_round_wins,
        "ties": ties,
        "game_winner": game_winner,
        "next_player1": game_winner,
        "round_details": rounds
    })

@app.route("/api/leaderboard", methods=["GET"])
def api_leaderboard():
    sort_mode = request.args.get("sort", "name")

    # 2) Leaderboard Presentation: convert dict -> list of dicts
    players_list = [
        {"name": name, **stats}
        for name, stats in LEADERBOARD.items()
    ]

    # Two distinct sorted views from the single list
    if sort_mode == "score":
        # high score first
        sorted_list = sorted(players_list, key=lambda x: x["score"], reverse=True)
    else:
        # alphabetical by name
        sorted_list = sorted(players_list, key=lambda x: x["name"].lower())

    return jsonify(sorted_list)

if __name__ == "__main__":
    app.run(debug=True)
