from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for
)

from database import db
from database.models import VoiceCreditChannel

import requests
import os
from dotenv import load_dotenv


load_dotenv()

API_BASE_URL = "https://discord.com/api"
BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)

GUILD_ID = os.getenv(
    "GUILD_ID"
)


def voice_credits_blueprint():

    voice_credits = Blueprint(
        "voice_credits",
        __name__,
        url_prefix="/voice-credits"
    )

    def is_admin():

        return bool(
            session.get("is_admin")
        )

    def get_discord_voice_channels():

        if not BOT_TOKEN:

            print(
                "Voice Credits: BOT_TOKEN fehlt."
            )

            return []

        if not GUILD_ID:

            print(
                "Voice Credits: GUILD_ID fehlt."
            )

            return []

        try:

            response = requests.get(

                f"{API_BASE_URL}"
                f"/guilds/{GUILD_ID}/channels",

                headers={
                    "Authorization":
                        f"Bot {BOT_TOKEN}"
                },

                timeout=10
            )

            if response.status_code != 200:

                print(
                    "Discord Channel API Fehler:",
                    response.status_code,
                    response.text
                )

                return []

            discord_channels = (
                response.json()
            )

            voice_channels = []

            for channel in discord_channels:

                if channel.get("type") != 2:

                    continue

                voice_channels.append({

                    "id":
                        channel.get("id"),

                    "name":
                        channel.get("name"),

                    "guild_id":
                        GUILD_ID

                })

            return voice_channels

        except Exception as e:

            print(
                "Discord Voice Channel Fehler:",
                e
            )

            return []


    @voice_credits.route(
        "/view",
        methods=["GET"]
    )
    def view():
        if not is_admin():

            return redirect(
                url_for("auth.login")
            )

        channels = (

            VoiceCreditChannel.query

            .order_by(
                VoiceCreditChannel.channel_name.asc()
            )

            .all()

        )

        discord_channels = (
            get_discord_voice_channels()
        )

        configured_channel_ids = [

            str(channel.channel_id)

            for channel in channels

        ]

        return render_template(

            "voice_credits/view.html",

            active="voice_credits",

            channels=
                channels,

            discord_channels=
                discord_channels,

            configured_channel_ids=
                configured_channel_ids

        )

    @voice_credits.route(
        "/create",
        methods=["POST"]
    )
    def create():
        if not is_admin():

            return jsonify({

                "success": False,

                "message":
                    "Keine Berechtigung."

            }), 403

        try:

            data = request.get_json()
            if not data:

                return jsonify({

                    "success": False,

                    "message":
                        "Keine Daten erhalten."

                }), 400

            channel_id = data.get(
                "channel_id"
            )

            credit_rate = data.get(
                "credit_rate"
            )

            try:

                channel_id = int(
                    channel_id
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "Ungültiger Voice-Channel."

                }), 400

            try:

                credit_rate = int(
                    credit_rate
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "Ungültige Credit-Anzahl."

                }), 400

            if credit_rate < 0:

                return jsonify({

                    "success": False,

                    "message":
                        "Die Credit-Anzahl darf "
                        "nicht negativ sein."

                }), 400

            discord_channels = (
                get_discord_voice_channels()
            )

            discord_channel = None

            for channel in discord_channels:

                try:

                    current_id = int(
                        channel["id"]
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    continue

                if current_id == channel_id:

                    discord_channel = (
                        channel
                    )

                    break

            if not discord_channel:

                return jsonify({

                    "success": False,

                    "message":
                        "Der Voice-Channel wurde "
                        "auf Discord nicht gefunden."

                }), 404

            existing = (

                VoiceCreditChannel.query

                .filter(
                    VoiceCreditChannel.channel_id ==
                    channel_id
                )

                .first()

            )

            if existing:

                return jsonify({

                    "success": False,

                    "message":
                        "Dieser Voice-Channel "
                        "ist bereits konfiguriert."

                }), 400

            try:

                guild_id = int(
                    GUILD_ID
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "GUILD_ID ist ungültig."

                }), 500

            channel = VoiceCreditChannel(

                guild_id=
                    guild_id,

                channel_id=
                    channel_id,

                channel_name=
                    discord_channel["name"],

                credit_rate=
                    credit_rate,

                enabled=True

            )

            db.session.add(
                channel
            )

            db.session.commit()

            return jsonify({

                "success": True,

                "message":
                    "Voice-Channel wurde hinzugefügt.",

                "id":
                    channel.id

            }), 201

        except Exception as e:

            db.session.rollback()

            print(
                "Voice Credit Create Fehler:",
                e
            )

            return jsonify({

                "success": False,

                "message":
                    "Fehler beim Erstellen."

            }), 500

    @voice_credits.route(
        "/edit",
        methods=["POST"]
    )
    def edit():
        if not is_admin():

            return jsonify({

                "success": False,

                "message":
                    "Keine Berechtigung."

            }), 403

        try:

            data = request.get_json()
            if not data:

                return jsonify({

                    "success": False,

                    "message":
                        "Keine Daten erhalten."

                }), 400

            entry_id = data.get(
                "id"
            )

            credit_rate = data.get(
                "credit_rate"
            )

            enabled = data.get(
                "enabled"
            )

            try:

                entry_id = int(
                    entry_id
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "Ungültiger Eintrag."

                }), 400

            channel = (

                VoiceCreditChannel.query

                .filter(
                    VoiceCreditChannel.id ==
                    entry_id
                )

                .first()

            )

            if not channel:

                return jsonify({

                    "success": False,

                    "message":
                        "Voice-Channel nicht gefunden."

                }), 404

            try:

                credit_rate = int(
                    credit_rate
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "Ungültige Credit-Anzahl."

                }), 400

            if credit_rate < 0:

                return jsonify({

                    "success": False,

                    "message":
                        "Die Credit-Anzahl darf "
                        "nicht negativ sein."

                }), 400

            channel.credit_rate = (
                credit_rate
            )

            if enabled is not None:

                channel.enabled = bool(
                    enabled
                )

            db.session.commit()

            return jsonify({

                "success": True,

                "message":
                    "Voice-Channel wurde geändert.",

                "credit_rate":
                    channel.credit_rate,

                "enabled":
                    channel.enabled

            })

        except Exception as e:

            db.session.rollback()

            print(
                "Voice Credit Edit Fehler:",
                e
            )

            return jsonify({

                "success": False,

                "message":
                    "Fehler beim Bearbeiten."

            }), 500


    @voice_credits.route(
        "/toggle",
        methods=["POST"]
    )
    def toggle():
        if not is_admin():

            return jsonify({

                "success": False,

                "message":
                    "Keine Berechtigung."

            }), 403

        try:

            data = request.get_json()
            if not data:

                return jsonify({

                    "success": False,

                    "message":
                        "Keine Daten erhalten."

                }), 400

            entry_id = data.get(
                "id"
            )

            try:

                entry_id = int(
                    entry_id
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "Ungültiger Eintrag."

                }), 400

            channel = (

                VoiceCreditChannel.query

                .filter(
                    VoiceCreditChannel.id ==
                    entry_id
                )

                .first()

            )

            if not channel:

                return jsonify({

                    "success": False,

                    "message":
                        "Voice-Channel nicht gefunden."

                }), 404

            channel.enabled = not bool(
                channel.enabled
            )

            db.session.commit()

            return jsonify({

                "success": True,

                "enabled":
                    channel.enabled,

                "message":
                    (
                        "Credit-Vergabe aktiviert."
                        if channel.enabled
                        else
                        "Credit-Vergabe deaktiviert."
                    )

            })

        except Exception as e:

            db.session.rollback()

            print(
                "Voice Credit Toggle Fehler:",
                e
            )

            return jsonify({

                "success": False,

                "message":
                    "Fehler beim Ändern."

            }), 500

    @voice_credits.route(
        "/delete",
        methods=["POST"]
    )
    def delete():

        if not is_admin():

            return jsonify({

                "success": False,

                "message":
                    "Keine Berechtigung."

            }), 403

        try:

            data = request.get_json()

            if not data:

                return jsonify({

                    "success": False,

                    "message":
                        "Keine Daten erhalten."

                }), 400

            entry_id = data.get(
                "id"
            )

            try:

                entry_id = int(
                    entry_id
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "Ungültiger Eintrag."

                }), 400

            channel = (

                VoiceCreditChannel.query

                .filter(
                    VoiceCreditChannel.id ==
                    entry_id
                )

                .first()

            )

            if not channel:

                return jsonify({

                    "success": False,

                    "message":
                        "Voice-Channel nicht gefunden."

                }), 404

            db.session.delete(
                channel
            )

            db.session.commit()

            return jsonify({

                "success": True,

                "message":
                    "Voice-Channel wurde gelöscht."

            })

        except Exception as e:

            db.session.rollback()

            print(
                "Voice Credit Delete Fehler:",
                e
            )

            return jsonify({

                "success": False,

                "message":
                    "Fehler beim Löschen."

            }), 500


    return voice_credits