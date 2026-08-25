from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for
)

from datetime import datetime

from database import db
from database.models import InternalDocument
from helper.perms import require_role_management


def document_blueprint():

    documents = Blueprint(
        "document",
        __name__,
        url_prefix="/document"
    )

    # ==========================================================
    # ÜBERSICHT
    # ==========================================================

    @documents.route("/view", methods=["GET"])
    def view():

        documents_list = (
            InternalDocument.query
            .order_by(
                InternalDocument.updated_at.desc()
            )
            .all()
        )

        return render_template(
            "document/view.html",
            active="document",
            documents=documents_list
        )

    # ==========================================================
    # DOKUMENT ANZEIGEN
    # ==========================================================

    @documents.route("/<int:document_id>", methods=["GET"])
    def detail(document_id):

        document = InternalDocument.query.get_or_404(
            document_id
        )

        return render_template(
            "document/detail.html",
            active="document",
            document=document
        )

    # ==========================================================
    # DOKUMENT ERSTELLEN
    # ==========================================================

    @documents.route("/create", methods=["GET", "POST"])
    @require_role_management
    def create():

        if not session.get("can_manage_roles"):
            return redirect(
                url_for("auth.login")
            )

        # ------------------------------------------
        # FORMULAR
        # ------------------------------------------

        if request.method == "GET":

            return render_template(
                "document/create.html",
                active="document"
            )

        # ------------------------------------------
        # JSON
        # ------------------------------------------

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

            content = data.get(
                "content",
                ""
            ).strip()

            if not title:
                return jsonify({
                    "success": False,
                    "message": "Bitte einen Titel angeben."
                }), 400

            if not content:
                return jsonify({
                    "success": False,
                    "message": "Der Dokumentinhalt darf nicht leer sein."
                }), 400

            document = InternalDocument(
                title=title,
                content=content
            )

            db.session.add(document)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Dokument wurde erfolgreich erstellt.",
                "document_id": document.id
            }), 201

        except Exception as e:

            db.session.rollback()

            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    # ==========================================================
    # DOKUMENT BEARBEITEN
    # ==========================================================

    @documents.route(
        "/<int:document_id>/edit",
        methods=["GET", "POST"]
    )
    @require_role_management
    def edit(document_id):

        if not session.get("can_manage_roles"):
            return redirect(
                url_for("auth.login")
            )

        document = InternalDocument.query.get_or_404(
            document_id
        )

        # ------------------------------------------
        # FORMULAR
        # ------------------------------------------

        if request.method == "GET":

            return render_template(
                "document/edit.html",
                active="document",
                document=document
            )

        # ------------------------------------------
        # JSON
        # ------------------------------------------

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

            content = data.get(
                "content",
                ""
            ).strip()

            if not title:
                return jsonify({
                    "success": False,
                    "message": "Bitte einen Titel angeben."
                }), 400

            if not content:
                return jsonify({
                    "success": False,
                    "message": "Der Dokumentinhalt darf nicht leer sein."
                }), 400

            document.title = title
            document.content = content
            document.updated_at = datetime.utcnow()

            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Dokument wurde erfolgreich gespeichert.",
                "document_id": document.id
            }), 200

        except Exception as e:

            db.session.rollback()

            return jsonify({
                "success": False,
                "message": str(e)
            }), 500
    
    # ==========================================================
    # DOKUMENT LÖSCHEN
    # ==========================================================

    @documents.route(
        "/<int:document_id>/delete",
        methods=["POST"]
    )
    @require_role_management
    def delete(document_id):

        if not session.get("can_manage_roles"):
            return redirect(
                url_for("auth.login")
            )

        document = InternalDocument.query.get_or_404(
            document_id
        )

        try:

            db.session.delete(document)
            db.session.commit()

            return jsonify({
                "success": True,
                "message": "Dokument wurde erfolgreich gelöscht."
            })

        except Exception as e:

            db.session.rollback()

            return jsonify({
                "success": False,
                "message": str(e)
            }), 500

    return documents