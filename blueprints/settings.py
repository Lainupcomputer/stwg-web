from flask import Blueprint, render_template, request, jsonify, session, url_for, redirect
from database import db
from database.models import DataStorage

settings_bp = Blueprint("settings", __name__, template_folder="", url_prefix="/settings")


@settings_bp.route("/", methods=["GET"])
def index():
    if session.get("is_admin"):
        return render_template("settings.html", active="settings")
    else:
        return redirect(url_for("index"))


def group_settings(settings: dict):
    grouped = {}

    for key, value in settings.items():
        if "." in key:
            group, subkey = key.split(".", 1)
        else:
            group = "general"
            subkey = key

        if group not in grouped:
            grouped[group] = {}

        grouped[group][subkey] = value

    return grouped


@settings_bp.route("/api", methods=["GET"])
def get_settings():
    if session.get("is_admin"):
        settings = DataStorage.query.all()
        settings_dict = {row.key: row.data for row in settings}

        return jsonify(group_settings(settings_dict))
    else:
        return redirect(url_for("index"))


@settings_bp.route("/api", methods=["POST"])
def update_settings():
    if session.get("is_admin"):
        new_settings = request.json
        for key, value in new_settings.items():
            row = DataStorage.query.filter_by(key=key).first()
            if row:
                row.data = value
            else:
                row = DataStorage(key=key, data=value)
                db.session.add(row)

        db.session.commit()
        return jsonify({"status": "ok"})
    else:
        return redirect(url_for("index"))
