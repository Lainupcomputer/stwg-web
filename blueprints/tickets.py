from flask import Blueprint, render_template, session, jsonify, redirect, url_for
from database.models import Ticket
from database import db

tickets_bp = Blueprint("tickets", __name__, url_prefix="/tickets")


@tickets_bp.route("/")
def tickets_page():
    if "user" not in session:
        return redirect(url_for("index"))
    return render_template("tickets.html", active="tickets")


@tickets_bp.route("/api")
def tickets_api():
    if "user" not in session:
        return redirect(url_for("index"))

    tickets = db.session.query(Ticket).order_by(Ticket.created_at.desc()).all()
    ticket_list = []
    for t in tickets:
        ticket_list.append({
            "id": t.id,
            "creator_id": t.creator_id,
            "creator_name": t.creator_name,
            "handler_id": t.handler_id,
            "description": t.description,
            "status": t.status,
            "created_at": t.created_at,
            "closed_at": t.closed_at,
            "is_locked": t.is_locked,
            "transcript": t.transcript
        })
    return jsonify(ticket_list)
