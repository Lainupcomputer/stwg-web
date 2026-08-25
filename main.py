from flask import Flask, redirect, url_for, session, request, render_template, flash, jsonify
import os
from database import db
from dotenv import load_dotenv
#from flask_session import Session
from database.models import UserProfile
from blueprints import register_blueprints
from blueprints.error_handler import register_error_handlers

from helper.db import get_user_profile_from_session, reload_user_permission



load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
register_error_handlers(app)
app.secret_key = os.getenv('SECRET_KEY')
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






@app.route("/")
def index():
    if not "user" in session:
        return render_template("main/index_not_logged_in.html")

    else:
        user = get_user_profile_from_session()
        if not user:
            return redirect(url_for("auth.logout"))

        reload_user_permission(user)

        return render_template("main/index.html", user=user, avatar_url=get_user_avatar_url(),
                               awards=json.loads(user.awards),
                               permissions=json.loads(user.licenses),
                              )




register_blueprints(app)
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
