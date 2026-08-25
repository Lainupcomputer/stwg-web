from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash
from database import db
from database.models import DataStorage, TeamMeeting
from dhooks import Webhook, Embed
from requests import HTTPError
from datetime import datetime
from helper.perms import require_role_management

def meeting_blueprint():
    meetings = Blueprint("meeting", __name__, url_prefix="/meeting")

    @meetings.route("/view", methods=["GET"])
    def view():
        meetings = (
            TeamMeeting.query
            .order_by(
                TeamMeeting.meeting_date.desc()
            )
            .all()
        )

        return render_template(
            "meeting/view.html",
            active="meeting",
            meetings=meetings
        )


    @meetings.route("/<int:meeting_id>", methods=["GET"])
    def detail(meeting_id):
        meeting = TeamMeeting.query.get_or_404(
            meeting_id
        )


        return render_template(
            "meeting/detail.html",
            active="meeting",
            meeting=meeting
        )


    @meetings.route("/create", methods=["GET", "POST"])
    @require_role_management
    def create():

        if not session.get("can_manage_roles"):
            return redirect(url_for("auth.login"))

        if request.method == "GET":
            return render_template(
                "meeting/create.html",
                active="meetings"
            )

        try:

            data = request.get_json()
            if not data:
                return jsonify({
                    "success": False,
                    "message": "Keine Daten erhalten."
                }), 400

            title = data.get(
                "title",
                ""
            ).strip()

            meeting_date = data.get(
                "meeting_date",
                ""
            ).strip()

            content = data.get(
                "content",
                ""
            ).strip()

            if not title:
                return jsonify({
                    "success": False,
                    "message": "Bitte einen Titel angeben."
                }), 400

            if not meeting_date:
                return jsonify({
                    "success": False,
                    "message": "Bitte ein Datum angeben."
                }), 400

            if not content:
                return jsonify({
                    "success": False,
                    "message": "Der Besprechungsinhalt darf nicht leer sein."
                }), 400

            try:
                meeting_date = datetime.strptime(
                    meeting_date,
                    "%Y-%m-%d"
                ).date()

            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "Ungültiges Datum."
                }), 400


            meeting = TeamMeeting(
                title=title, meeting_date=meeting_date, content=content ) 
            db.session.add(meeting)
            db.session.commit() 
            return jsonify({ "success": True, "message": "Besprechung wurde erfolgreich gespeichert.", "meeting_id": meeting.id }), 201


        except Exception as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 500


    @meetings.route("/announce", methods=["GET", "POST"])
    @require_role_management
    def announce():
        if request.method == "GET":

            return render_template(
                "meeting/announce.html",
                active="meeting"
            )

        meeting_date = request.form.get(
            "meeting_date",
            ""
        ).strip()

        meeting_time = request.form.get(
            "meeting_time",
            ""
        ).strip()

        if not meeting_date:

            flash(
                "Bitte ein Datum für die Besprechung auswählen.",
                "error"
            )

            return redirect(
                url_for("meeting.announce")
            )


        if not meeting_time:

            flash(
                "Bitte eine Uhrzeit für die Besprechung auswählen.",
                "error"
            )

            return redirect(
                url_for("meeting.announce")
            )

        user_announcement_hook_url = (
            DataStorage.query
            .filter_by(
                key="hooks.announcement_hook_url"
            )
            .first()
        )

        if not user_announcement_hook_url:

            flash(
                "Konnte Announcement nicht senden, "
                "Webhook URL ist nicht vorhanden.",
                "error"
            )

            return redirect(
                url_for("meeting.announce")
            )

        if not user_announcement_hook_url.data:

            flash(
                "Konnte Announcement nicht senden, "
                "Webhook URL ist leer.",
                "error"
            )

            return redirect(
                url_for("meeting.announce")
            )

        try:

            announcement_hook = Webhook(
                user_announcement_hook_url.data
            )

            announcement_embed = Embed(

                title="📢 Ankündigung der nächsten Besprechung",

                description=(
                    "Wir möchten euch informieren, dass "
                    "die nächste **Besprechung** am "
                    f"**{meeting_date}** um "
                    f"**{meeting_time} Uhr** stattfindet.\n\n"
                    "Anwesenheit ist erwünscht, "
                    "aber keine Pflicht!"
                ),

                color=0x992D22
            )

            announcement_embed.set_footer(
                text="Danke für eure Aufmerksamkeit!"
            )
            announcement_hook.send(
                embed=announcement_embed
            )
            flash(
                "Die Besprechung wurde erfolgreich angekündigt.",
                "success"
            )


        except HTTPError:

            flash(
                "Konnte Announcement nicht senden, "
                "Webhook URL ist falsch.",
                "error"
            )


        except ValueError:

            flash(
                "Konnte Announcement nicht senden, "
                "Webhook URL ist nicht vorhanden oder ungültig.",
                "error"
            )


        except Exception as e:

            print(
                "Fehler beim Senden des Announcements:",
                e
            )

            flash(
                "Beim Senden des Announcements ist ein "
                "unerwarteter Fehler aufgetreten.",
                "error"
            )

        return redirect(
            url_for("meeting.announce")
        )

    return meetings