from flask import Blueprint, request, session, redirect, url_for, flash
import requests
import os
from dotenv import load_dotenv
load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
API_BASE_URL = "https://discord.com/api"
GUILD_ID = os.getenv('GUILD_ID')


# auth helper



def auth_blueprint():
    auth = Blueprint("auth", __name__, url_prefix="/auth")

    @auth.route("/login")
    def login():
        if session.get("user"):
            flash("Du has Keine Berechtigungen")
            return redirect(url_for("index"))

        oauth_url = (
            f"{API_BASE_URL}/oauth2/authorize"
            f"?client_id={CLIENT_ID}"
            f"&redirect_uri={REDIRECT_URI}"
            f"&response_type=code"
            f"&scope=identify%20guilds%20guilds.members.read"
        )
        return redirect(oauth_url)

    @auth.route("/logout")
    def logout():
        if session.get("user"):
            session.clear()
        return redirect(url_for("index"))

    @auth.route("/callback")
    def callback():
        # Wenn der Login abgebrochen wurde
        if "error" in request.args:
            # Optional: Fehlermeldung anzeigen
            return redirect(url_for("index"))  # oder eigenes Template
        code = request.args.get("code")

        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
        }

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        token_res = requests.post(f"{API_BASE_URL}/oauth2/token", data=data, headers=headers)
        token_res.raise_for_status()
        tokens = token_res.json()

        access_token = tokens["access_token"]

        # User speichern
        user_res = requests.get(
            f"{API_BASE_URL}/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        session["user"] = user_res.json()
        session.permanent = True

        member_res = requests.get(
            f"{API_BASE_URL}/users/@me/guilds/{GUILD_ID}/member",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        if member_res.status_code != 200:
            session["can_manage_roles"] = False
            return redirect(url_for("index"))

        member = member_res.json()

        # Member-Roles IDs:
        role_ids = member.get("roles", [])

        # ➤ Jetzt brauchst du die Guild Roles (vom Bot!):
        bot_token = os.getenv("BOT_TOKEN")
        roles_res = requests.get(
            f"{API_BASE_URL}/guilds/{GUILD_ID}/roles",
            headers={"Authorization": f"Bot {bot_token}"}
        )
        roles = roles_res.json()


        # Checken, ob eine der Rollen manage_roles gesetzt hat
        MANAGE_ROLES = 1 << 28  # Permission bit
        has_permission = False
        for role in roles:

            if role["id"] in role_ids:
                if role["permissions"] & MANAGE_ROLES:
                    has_permission = True
                    break

        session["can_manage_roles"] = has_permission

        return redirect(url_for("index"))

    return auth
