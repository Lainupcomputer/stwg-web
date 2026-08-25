from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    session,
    redirect,
    url_for
)

from sqlalchemy import desc
from database import db
from database.models import WaspHighscore


def wasp_blueprint() -> Blueprint:
    wasp = Blueprint("wasp", __name__, url_prefix="/wasp")

    def get_current_user():
        user = session.get("user")
        if not user:
            return None

        user_id = user.get("id")

        username = (
            user.get("global_name")
            or user.get("username")
            or "Unbekannt"
        )

        if not user_id:
            return None

        return {
            "user_id": str(user_id),
            "username": username
        }


    @wasp.route("/")
    def game():
            if "user" in session:
                return render_template(
                    "wasp_game/wasp_game.html", active="wasp_game"
                )
            else:
                return redirect(url_for("auth.login"))


    @wasp.route(
        "/api/game-over",
        methods=["POST"]
    )
    def game_over():
        user = get_current_user()

        if not user:
            return jsonify({
                "success": False,
                "error": "Nicht eingeloggt"
            }), 401

        user_id = user["user_id"]
        username = user["username"]

        data = request.get_json(
            silent=True
        ) or {}

        try:

            score = int(
                data.get(
                    "score",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            score = 0

        score = max(
            0,
            score
        )

        player = (
            WaspHighscore.query
            .filter_by(
                user_id=user_id
            )
            .first()
        )

        if player is None:

            player = WaspHighscore(
                user_id=user_id,
                username=username,
                highscore=score,
                games_played=1
            )

            db.session.add(
                player
            )

        else:

            player.username = username
            player.games_played += 1
            if score > player.highscore:

                player.highscore = score

        db.session.commit()


        return jsonify({

            "success": True,

            "score": score,

            "highscore": player.highscore,

            "games_played":
                player.games_played

        })

    @wasp.route("/api/my-score")
    def my_score():
        user = get_current_user()

        if not user:

            return jsonify({
                "success": False,
                "error": "Nicht eingeloggt"
            }), 401

        user_id = user["user_id"]

        player = (
            WaspHighscore.query
            .filter_by(
                user_id=user_id
            )
            .first()
        )

        if player is None:

            return jsonify({

                "success": True,

                "highscore": 0,

                "games_played": 0

            })

        return jsonify({

            "success": True,

            "highscore":
                player.highscore,

            "games_played":
                player.games_played

        })


    @wasp.route("/api/leaderboard")
    def leaderboard():

        players = (

            WaspHighscore.query

            .order_by(

                desc(
                    WaspHighscore.highscore
                ),

                WaspHighscore.games_played

            )

            .limit(100)

            .all()

        )


        return jsonify([

            {

                "rank": index + 1,

                "username":
                    player.username,

                "highscore":
                    player.highscore,

                "games_played":
                    player.games_played

            }

            for index, player
            in enumerate(players)

        ])

    @wasp.route("/leaderboard")
    def leaderboard_page():

        return render_template(
            "wasp_game/wasp_leaderboard.html", active="wasp_game"
        )
    return wasp