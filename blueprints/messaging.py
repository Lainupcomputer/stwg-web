from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    flash,
    session
)
from database import db
from database.models import MessagePreset, UserProfile, DataStorage, ActionQueue, DMMessage
from dhooks import Webhook, Embed
from helper.perms import require_role_management, require_support_permission
from requests import HTTPError

import json


messaging_bp = Blueprint(
    "messaging",
    __name__,
    template_folder="templates"
)

# ---------------------------------------------------
# PAGE
# ---------------------------------------------------
@messaging_bp.get("/")
@require_support_permission
def messaging_page():
    # Nutzerliste aus DB
    users = UserProfile.query.order_by(UserProfile.username).all()
    users_data = [{"id": u.user_id, "username": u.username} for u in users]
    return render_template("messaging.html", users=users_data, active='messaging')




@messaging_bp.get("/api/messages")
@require_support_permission
def get_messages():
    msgs = DMMessage.query.all()
    return jsonify([x.as_dict() for x in msgs])

# ---------------------------------------------------
# PRESETS – API
# ---------------------------------------------------
@messaging_bp.get("/api/presets")
@require_support_permission
def get_presets():
    p = MessagePreset.query.all()
    return jsonify([x.as_dict() for x in p])


@messaging_bp.post("/api/presets")
@require_support_permission
def add_preset():
    data = request.json
    p = MessagePreset(
        type=data["type"],
        title=data["title"],
        text=data["text"]
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"status": "ok", "id": p.id})


@messaging_bp.put("/api/presets/<int:id>")
@require_support_permission
def update_preset(id):
    p = MessagePreset.query.get(id)
    data = request.json

    p.title = data["title"]
    p.text = data["text"]
    p.type = data["type"]

    db.session.commit()
    return jsonify({"status": "ok"})


@messaging_bp.delete("/api/presets/<int:id>")
@require_support_permission
def delete_preset(id):
    p = MessagePreset.query.get(id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({"status": "ok"})


# ---------------------------------------------------
# SENDEN – API
# ---------------------------------------------------
@messaging_bp.post("/api/send/announcement")
@require_support_permission
def send_announcement():
    text = request.json["text"]
    user_announcement_hook_url = DataStorage.query.filter_by(key="hooks.announcement_hook_url").first()
    announcement_hook = Webhook(user_announcement_hook_url.data)
    announcement_embed = Embed(title="📢 Ankündigung", description=text, color=0x992D22)
    announcement_embed.set_footer(text="Danke für eure Aufmerksamkeit!")

    try:
        announcement_hook.send(embed=announcement_embed)
        flash("Announcement gesendet.")
        return jsonify({"status": "ok"})
    except HTTPError:
        flash("Konnte Announcement nicht senden, Webhook Url ist Falsch.")
        return jsonify({"status": "failed, url wrong"})
    except ValueError:
        flash("Konnte Announcement nicht senden, Webhook Url ist nicht  vorhanden.")
        return jsonify({"status": "faild, Value error"})


@messaging_bp.post("/api/send/user")
@require_support_permission
def send_user():

    data = request.get_json() or {}

    user_id = data.get("userId")
    text = data.get("text", "").strip()

    append_sender = bool(
        data.get("append_sender", False)
    )

    append_leadership = bool(
        data.get("append_leadership", False)
    )


    if not user_id:
        return jsonify({
            "error": "Kein Nutzer ausgewählt."
        }), 400


    if not text:
        return jsonify({
            "error": "Keine Nachricht eingegeben."
        }), 400


    # ==================================================
    # EMPFÄNGER AUS DB LADEN
    # ==================================================

    user = UserProfile.query.filter_by(
        user_id=user_id
    ).first()


    if not user:
        return jsonify({
            "error": "Nutzer wurde nicht gefunden."
        }), 404


    # ==================================================
    # USERNAME PLATZHALTER
    # ==================================================
    #
    # !USERNAM! wird durch den Username
    # des Empfängers ersetzt.
    #
    # Beispiel:
    #
    # "Hallo !USERNAM!, deine Ausbildung..."
    #
    # wird zu:
    #
    # "Hallo Lain, deine Ausbildung..."
    #
    # ==================================================

    username = user.username or "Unbekannt"

    text = text.replace(
        "!USERNAME!",
        username
    )


    # ==================================================
    # ABSENDER
    # ==================================================

    if append_sender:

        # Discord-OAuth-Daten liegen in session["user"]
        sender_id = session.get(
            "user",
            {}
        ).get("id")


        if sender_id:

            text += (
                f"\n\n<@{sender_id}>"
            )


    # ==================================================
    # LEITUNG
    # ==================================================

    if append_leadership:

        leadership_mentions = []

        users = UserProfile.query.all()


        for user_profile in users:

            licenses = user_profile.licenses or []


            # Falls licenses als JSON-String gespeichert ist
            if isinstance(licenses, str):

                try:

                    licenses = json.loads(
                        licenses
                    )

                except (
                    json.JSONDecodeError,
                    TypeError
                ):

                    continue


            # Sicherheit:
            # Nur Listen verarbeiten
            if not isinstance(
                licenses,
                list
            ):

                continue


            for license_data in licenses:

                if not isinstance(
                    license_data,
                    dict
                ):

                    continue


                if (
                    license_data.get("name")
                    == "Leitung"

                    and

                    license_data.get("has")
                    is True
                ):

                    if user_profile.user_id:

                        leadership_mentions.append(
                            f"<@{user_profile.user_id}>"
                        )

                    break


        if leadership_mentions:

            text += (
                "\n\n"
                + " ".join(
                    leadership_mentions
                )
            )


    # ==================================================
    # ACTION QUEUE
    # ==================================================

    action = ActionQueue(
        key="send_user_message",
        data={
            "userId": user_id,
            "text": text
        }
    )


    # ==================================================
    # ADMIN LOG / WEBHOOK
    # ==================================================

    admin_announcement_hook_url = DataStorage.query.filter_by(
        key="hooks.admin_announcement_hook_url"
    ).first()


    if admin_announcement_hook_url:

        announcement_hook = Webhook(
            admin_announcement_hook_url.data
        )


        embed = Embed(
            title=f"📢 Nachricht gesendet an: {username}",
            description=text,
            color=0x992D22
        )


        announcement_hook.send(
            embed=embed
        )


    # ==================================================
    # SPEICHERN
    # ==================================================

    db.session.add(
        action
    )

    db.session.commit()


    return jsonify({
        "status": "ok"
    })
