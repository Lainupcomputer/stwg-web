from flask import Flask, redirect, url_for, session, request, render_template, flash, jsonify
import os
from database import db
from dotenv import load_dotenv
#from flask_session import Session
from database.models import UserProfile, DataStorage
from blueprints import register_blueprints
from blueprints.error_handler import register_error_handlers
from helper.perms import has_license

from dhooks import Webhook

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
register_error_handlers(app)
app.secret_key = "os.urandom(24)"
from datetime import timedelta
import json


app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = db
app.config['SESSION_SQLALCHEMY_TABLE'] = 'sessions'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_USE_SIGNER'] = True


##### Main seie dara
def get_user_avatar_url() -> str:
    if session["user"]["avatar"]:
        return f'https://cdn.discordapp.com/avatars/{session["user"]['id']}/{session["user"]['avatar']}.png?size=256'
    else:
        return f"https://cdn.discordapp.com/embed/avatars/0.png"

permissions=[{"name": "Flugausbildung", "has": True,  "description": "Seit über 1 Jahr dabei"},
             {"name": "Leitung", "has": True},
             {"name": "Auftragsbearbeitung", "has": True},
             {"name": "Supporter", "has": False},
             {"name": "Zustechen", "has": True},
             {"name": "Ausbilder", "has": True},
             {"name": "Mitglied", "has": True},]

awards = [{"name": "Anderson Award", "has": True,  "description": "Sei der Wahre"},
          {"name": "Aktivster der Monats", "has": False,  "description": "Der Aktivste diesen Monat"},
          {"name": "Leitung", "has": True,  "description": "War mal in der Clanleitung"},
          {"name": "Designer", "has": True,  "description": "Hat einen Skin erstellt"}
        ]


def reload_user_permission(user: UserProfile):
            session["is_trainer"] = has_license(
            user, "Ausbilder")
            session["is_supporter"] = has_license(
            user, "Supporter")
            session["is_admin"] = has_license(
            user, "Leitung")





@app.route("/")
def index():
    import logging
    logger = logging.getLogger()
    if "user" in session:
        user = UserProfile.query.filter_by(user_id=session["user"]["id"]).first()
        if not user:
            return redirect(url_for("auth.logout"))

        logger.error(session)
        reload_user_permission(user)

        return render_template("main/index.html", user=user, avatar_url=get_user_avatar_url(),
                               awards=json.loads(user.awards),
                               permissions=json.loads(user.licenses),
                              )

    else:
        return render_template("main/index_not_logged_in.html")


@app.route("/profile/action", methods=["POST"])
def profile_action():
    data = request.get_json()

    admin_announcement_hook_url = DataStorage.query.filter_by(
        key="hooks.admin_announcement_hook_url"
    ).first()

    if not admin_announcement_hook_url or not admin_announcement_hook_url.data:
        return jsonify({
            "error": "Admin-Webhook ist nicht konfiguriert"
        }), 500

    admin_hook = Webhook(
        admin_announcement_hook_url.data
    )

    user_id = session["user"]["id"]

    if not data:
        return jsonify({
            "error": "Keine Daten empfangen"
        }), 400


    if "endDate" in data:

        action_type = "Abwesenheit"

        end_date = data.get("endDate")

        admin_hook.send(
            f"<@{user_id}> hat sich Abwesend gemeldet bis : {end_date}"
        )


    elif "topic" in data and "desiredDate" in data:

        action_type = "Leitungsgespräch"

        topic = data.get("topic")

        desired_date = data.get("desiredDate")

        admin_hook.send(
            f"<@{user_id}> wünscht ein Leitungsgespräch "
            f"am {desired_date} zum Thema {topic}"
        )


    elif "trainingName" in data and "trainingDate" in data:

        action_type = "Ausbildung planen"

        training_name = data.get("trainingName")

        training_date = data.get("trainingDate")

        hook = Webhook("https://discord.com/api/webhooks/1541292917044285552/WGDxwT8KZh6tgaW3sN_e3o1KQQP7bFy1BJ93Duua2ySCyvB-Pqg9BtcjPuHoWrvke_5-")

        hook.send(
            f"<@{user_id}> möchte eine Ausbildung planen: "
            f"{training_name} am {training_date}"
        )


    elif "changeRequest" in data:

        action_type = "Änderung Anfragen"

        change_request = data.get("changeRequest")

        admin_hook.send(
            f"<@{user_id}> wünscht eine Änderung: "
            f"{change_request}"
        )


    else:

        return jsonify({
            "error": "Unbekannter Datentyp"
        }), 400


    return jsonify({
        "status": "ok",
        "action": action_type
    })

register_blueprints(app)
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
