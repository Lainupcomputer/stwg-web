from flask import Blueprint, request, jsonify, render_template, session, url_for, redirect
from database.models import StatusMessage
from database import db


def status_blueprint() -> Blueprint:
    status = Blueprint("status", __name__)

    @status.route("/", methods=["GET"])
    def get_status_messages():
        if session.get("is_admin"):
            messages = StatusMessage.query.all()
            return jsonify([{"id": m.id, "message": m.message} for m in messages])
        else:
            return redirect(url_for("index"))

    @status.route("/", methods=["POST"])
    def create_status_message():
        if session.get("is_admin"):
            data = request.get_json() or request.form

            if not data or "message" not in data:
                return jsonify({"error": "Missing 'message' field"}), 400

            new_msg = StatusMessage(message=data["message"])
            db.session.add(new_msg)
            db.session.commit()
            return jsonify({"id": new_msg.id, "message": new_msg.message}), 201
        else:
            return redirect(url_for("index"))

    @status.route("/<int:msg_id>", methods=["PUT"])
    def update_status_message(msg_id):
        if session.get("is_admin"):
            data = request.get_json()

            if not data or "message" not in data:
                return jsonify({"error": "Missing 'message' field"}), 400

            msg = StatusMessage.query.get(msg_id)
            if not msg:
                return jsonify({"error": "Message not found"}), 404

            msg.message = data["message"]
            db.session.commit()
            return jsonify({"id": msg.id, "message": msg.message})
        else:
            return redirect(url_for("index"))

    @status.route("/<int:msg_id>", methods=["DELETE"])
    def delete_status_message(msg_id):
        if session.get("is_admin"):
            msg = StatusMessage.query.get(msg_id)

            if not msg:
                return jsonify({"error": "Message not found"}), 404

            db.session.delete(msg)
            db.session.commit()
            return jsonify({"message": "Deleted successfully"})

        else:
            return redirect(url_for("index"))

    @status.route("/view")
    def status_page():
        if session.get("is_admin"):
            messages = StatusMessage.query.all()
            return render_template("status.html", messages=messages, active="status")
        else:
            return redirect(url_for("index"))

    return status
