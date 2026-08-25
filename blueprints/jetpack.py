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
from database.models import JetpackHighscore


def jetpack_blueprint() -> Blueprint:

    jetpack = Blueprint(
        "jetpack",
        __name__,
        url_prefix="/jetpack"
    )


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


    # ==========================================================
    # SPIEL
    # ==========================================================

    @jetpack.route("/")
    def game():

        if "user" in session:

            return render_template(
                "jetpack_game/jetpack_game.html",
                active="jetpack_game"
            )

        return redirect(
            url_for("auth.login")
        )


    # ==========================================================
    # GAME OVER / SCORE SPEICHERN
    # ==========================================================

    @jetpack.route(
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
            JetpackHighscore.query
            .filter_by(
                user_id=user_id
            )
            .first()
        )


        # Neuer Spieler
        if player is None:

            player = JetpackHighscore(

                user_id=user_id,

                username=username,

                highscore=score,

                games_played=1

            )


            db.session.add(
                player
            )


        # Bestehender Spieler
        else:

            player.username = username

            player.games_played += 1


            if score > player.highscore:

                player.highscore = score


        db.session.commit()


        return jsonify({

            "success": True,

            "score": score,

            "highscore":
                player.highscore,

            "games_played":
                player.games_played

        })


    # ==========================================================
    # EIGENER HIGHSCORE
    # ==========================================================

    @jetpack.route(
        "/api/my-score"
    )
    def my_score():

        user = get_current_user()


        if not user:

            return jsonify({

                "success": False,

                "error":
                    "Nicht eingeloggt"

            }), 401


        user_id = user["user_id"]


        player = (
            JetpackHighscore.query
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


    # ==========================================================
    # LEADERBOARD API
    # ==========================================================

    @jetpack.route(
        "/api/leaderboard"
    )
    def leaderboard():

        players = (

            JetpackHighscore.query

            .order_by(

                desc(
                    JetpackHighscore.highscore
                ),

                JetpackHighscore.games_played

            )

            .limit(100)

            .all()

        )


        return jsonify([

            {

                "rank":
                    index + 1,

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


    # ==========================================================
    # LEADERBOARD SEITE
    # ==========================================================

    @jetpack.route(
        "/leaderboard"
    )
    def leaderboard_page():

        return render_template(

            "jetpack_game/jetpack_leaderboard.html",

            active="jetpack_game"

        )


    return jetpack