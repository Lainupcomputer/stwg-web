from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for
)
from dhooks import Webhook
from database import db
from database.models import (
    UserProfile,
    Comment,
    Warning,
    GroupAction,
    DataStorage

)
 
from sqlalchemy.orm import selectinload
from helper.perms import require_admin_permission


def user_blueprint():

    user = Blueprint(
        "users",
        __name__,
        url_prefix="/users"
    )


    # ==========================================================
    # BENUTZER VERWALTUNG
    # ==========================================================

    @user.route("/view", methods=["GET"])
    @require_admin_permission
    def view_users():
        return render_template(
            "users.html",
            active="user"
        )


    # ==========================================================
    # ALLE USER
    # ==========================================================

    @user.route("/", methods=["GET"])
    @require_admin_permission
    def get_users():
        users = (
            UserProfile.query
            .options(
                selectinload(UserProfile.comments),
                selectinload(UserProfile.warnings),
                selectinload(UserProfile.group_actions)
            )
            .all()
        )


        result = []


        for u in users:

            result.append({

                "id": u.id,

                "user_id": u.user_id,

                "username": u.username,

                "join_date": u.join_date,

                "last_uprank": u.last_uprank,

                "status": u.status,

                "online_time": u.currency_total,

                "has_payed": u.has_payed,

                "is_member": u.is_member,


                # ==========================================
                # KOMMENTARE
                # ==========================================

                "comments": [
                    {
                        "id": c.id,
                        "author": c.author,
                        "comment": c.comment
                    }
                    for c in u.comments
                ],


                # ==========================================
                # WARNINGS
                # ==========================================

                "warnings": [
                    {
                        "id": w.id,
                        "time": w.time,
                        "comment": w.comment
                    }
                    for w in u.warnings
                ],


                # ==========================================
                # GROUP ACTIONS
                # ==========================================

                "group_actions": [
                    {
                        "id": g.id,
                        "time": g.time,
                        "action": g.action
                    }
                    for g in u.group_actions
                ],


                # ==========================================
                # COUNTS
                # ==========================================

                "comments_count": len(u.comments),

                "warnings_count": len(u.warnings),

                "actions_count": len(u.group_actions)

            })


        return jsonify(result)


    # ==========================================================
    # EINEN USER
    # ==========================================================

    @user.route("/<int:id>", methods=["GET"])
    @require_admin_permission
    def get_user(id):
        user = (
            UserProfile.query
            .options(
                selectinload(UserProfile.comments),
                selectinload(UserProfile.warnings),
                selectinload(UserProfile.group_actions)
            )
            .filter_by(id=id)
            .first()
        )


        if not user:

            return jsonify({
                "error": "User nicht gefunden"
            }), 404


        return jsonify({

            "id": user.id,

            "user_id": user.user_id,

            "username": user.username,

            "join_date": user.join_date,

            "last_uprank": user.last_uprank,

            "status": user.status,

            "online_time": user.currency_total,

            "has_payed": user.has_payed,

            "is_member": user.is_member,


            "comments": [
                {
                    "id": c.id,
                    "author": c.author,
                    "comment": c.comment
                }
                for c in user.comments
            ],


            "warnings": [
                {
                    "id": w.id,
                    "time": w.time,
                    "comment": w.comment
                }
                for w in user.warnings
            ],


            "group_actions": [
                {
                    "id": g.id,
                    "time": g.time,
                    "action": g.action
                }
                for g in user.group_actions
            ]

        })


    # ==========================================================
    # USER BEARBEITEN
    # ==========================================================

    @user.route("/<int:id>", methods=["PUT"])
    @require_admin_permission
    def update_user(id):
        user = UserProfile.query.get(id)
        if not user:

            return jsonify({
                "error": "User nicht gefunden"
            }), 404


        data = request.get_json()


        if not data:

            return jsonify({
                "error": "Keine Daten übergeben"
            }), 400


        if "username" in data:
            user.username = data["username"]


        if "join_date" in data:
            user.join_date = data["join_date"]


        if "last_uprank" in data:
            user.last_uprank = data["last_uprank"]


        if "status" in data:
            user.status = data["status"]


        if "has_payed" in data:
            user.has_payed = data["has_payed"]


        if "is_member" in data:
            user.is_member = data["is_member"]


        db.session.commit()


        return jsonify({
            "success": True,
            "message": "User aktualisiert"
        })


    # ==========================================================
    # USER LÖSCHEN
    # ==========================================================

    @user.route("/<int:id>", methods=["DELETE"])
    @require_admin_permission
    def delete_user(id):
        user = UserProfile.query.get(id)
        if not user:

            return jsonify({
                "error": "User nicht gefunden"
            }), 404


        db.session.delete(user)

        db.session.commit()


        return jsonify({
            "success": True,
            "message": "User gelöscht"
        })


    # ==========================================================
    # KOMMENTAR HINZUFÜGEN
    # ==========================================================

    @user.route("/<int:id>/comments", methods=["POST"])
    @require_admin_permission
    def add_comment(id):
        user = UserProfile.query.get(id)
        if not user:

            return jsonify({
                "error": "User nicht gefunden"
            }), 404


        data = request.get_json()


        if (
            not data
            or "author" not in data
            or "comment" not in data
        ):

            return jsonify({
                "error": "Fehlende Felder"
            }), 400


        comment = Comment(
            user=user,
            author=data["author"],
            comment=data["comment"]
        )


        db.session.add(comment)

        db.session.commit()


        return jsonify({

            "success": True,

            "message": "Kommentar hinzugefügt",

            "id": comment.id

        }), 201


    # ==========================================================
    # KOMMENTAR LÖSCHEN
    # ==========================================================

    @user.route("/comments/<int:comment_id>", methods=["DELETE"])
    @require_admin_permission
    def delete_comment(comment_id):
        comment = Comment.query.get(comment_id)
        if not comment:

            return jsonify({
                "error": "Kommentar nicht gefunden"
            }), 404


        db.session.delete(comment)

        db.session.commit()


        return jsonify({
            "success": True,
            "message": "Kommentar gelöscht"
        })


    # ==========================================================
    # WARNING HINZUFÜGEN
    # ==========================================================

    @user.route("/<int:id>/warnings", methods=["POST"])
    @require_admin_permission
    def add_warning(id):
        user = UserProfile.query.get(id)
        if not user:

            return jsonify({
                "error": "User nicht gefunden"
            }), 404


        data = request.get_json()


        if not data or "comment" not in data:

            return jsonify({
                "error": "Fehlende Felder"
            }), 400


        warning = Warning(
            user=user,
            comment=data["comment"]
        )


        db.session.add(warning)

        db.session.commit()


        return jsonify({

            "success": True,

            "message": "Warning hinzugefügt",

            "id": warning.id

        }), 201


    # ==========================================================
    # WARNING LÖSCHEN
    # ==========================================================

    @user.route("/warnings/<int:warning_id>", methods=["DELETE"])
    @require_admin_permission
    def delete_warning(warning_id):
        warning = Warning.query.get(warning_id)
        if not warning:

            return jsonify({
                "error": "Warning nicht gefunden"
            }), 404


        db.session.delete(warning)

        db.session.commit()


        return jsonify({
            "success": True,
            "message": "Warning gelöscht"
        })


    # ==========================================================
    # GROUP ACTION HINZUFÜGEN
    # ==========================================================

    @user.route("/<int:id>/group_actions", methods=["POST"])
    @require_admin_permission
    def add_group_action(id):
        user = UserProfile.query.get(id)
        if not user:

            return jsonify({
                "error": "User nicht gefunden"
            }), 404


        data = request.get_json()


        if not data or "action" not in data:

            return jsonify({
                "error": "Fehlende Felder"
            }), 400


        group_action = GroupAction(
            user=user,
            action=data["action"]
        )


        db.session.add(group_action)

        db.session.commit()


        return jsonify({

            "success": True,

            "message": "GroupAction hinzugefügt",

            "id": group_action.id

        }), 201


    # ==========================================================
    # GROUP ACTION LÖSCHEN
    # ==========================================================

    @user.route(
        "/group_actions/<int:action_id>",
        methods=["DELETE"]
    )
    @require_admin_permission
    def delete_group_action(action_id):
        action = GroupAction.query.get(action_id)
        if not action:

            return jsonify({
                "error": "GroupAction nicht gefunden"
            }), 404


        db.session.delete(action)

        db.session.commit()


        return jsonify({
            "success": True,
            "message": "GroupAction gelöscht"
        })


    # ==========================================================
    # ALLE BEITRÄGE ZURÜCKSETZEN
    # ==========================================================

    @user.route(
        "/reset-payments",
        methods=["PUT"]
    )
    @require_admin_permission
    def reset_payments():
        users = UserProfile.query.all()
        for user in users:

            user.has_payed = False


        db.session.commit()


        return jsonify({

            "success": True,

            "message": "Alle Beiträge zurückgesetzt"

        })


    @user.route("/action", methods=["POST"])
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

            hook = Webhook(DataStorage.query.filter_by(
            key="hooks.training_hook_url"
            ).first().data)

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


    return user