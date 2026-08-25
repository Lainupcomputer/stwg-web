from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash
)

from datetime import datetime
from sqlalchemy import func
import logging

from database import db
from database.models import (
    UserProfile,
    Training,
    TrainingCompletion
)


# ==========================================================
# BLUEPRINT
# ==========================================================

training_bp = Blueprint(
    "training",
    __name__,
    url_prefix="/training"
)


# ==========================================================
# HILFSFUNKTIONEN
# ==========================================================

def is_admin():
    """
    Prüft, ob der aktuelle Benutzer
    Ausbildungsverwaltung verwenden darf.
    """

    return session.get(
        "is_trainer",
        False
    )


def current_month():
    """
    Gibt das aktuelle Jahr und den aktuellen Monat zurück.
    """

    now = datetime.now()

    return now.year, now.month


def get_active_members():
    """
    Gibt alle aktiven Mitglieder zurück.
    """

    return (
        UserProfile.query
        .filter_by(is_member=True)
        .order_by(
            UserProfile.username.asc()
        )
        .all()
    )


def get_month_completion(
    user_id,
    training_id,
    year=None,
    month=None
):
    """
    Prüft, ob ein Mitglied eine Ausbildung
    im angegebenen Monat absolviert hat.

    user_id ist die interne UserProfile.id.
    """

    if year is None or month is None:
        year, month = current_month()

    return (
        TrainingCompletion.query
        .filter_by(
            user_id=user_id,
            training_id=training_id,
            year=year,
            month=month
        )
        .first()
    )


def training_completed_this_month(
    user_id,
    training_id
):
    """
    Convenience-Funktion für den aktuellen Monat.
    """

    return get_month_completion(
        user_id,
        training_id
    ) is not None


def get_required_trainings():
    """
    Gibt alle aktiven monatlich verpflichtenden
    Ausbildungen zurück.
    """

    return (
        Training.query
        .filter_by(
            active=True,
            required_monthly=True
        )
        .order_by(
            Training.name.asc()
        )
        .all()
    )


def get_training_status(
    user,
    training,
    year,
    month
):
    """
    Gibt den Status einer Ausbildung
    für einen Benutzer zurück.
    """

    completion = get_month_completion(
        user.id,
        training.id,
        year,
        month
    )

    if completion:

        return {
            "completed": True,
            "completion": completion
        }

    return {
        "completed": False,
        "completion": None
    }


# ==========================================================
# ÜBERSICHT
# ==========================================================

@training_bp.route("/")
def index():

    if not is_admin():
        return "Keine Berechtigung", 403

    year, month = current_month()

    members = get_active_members()

    required_trainings = get_required_trainings()

    total_required = (
        len(members) *
        len(required_trainings)
    )

    completed = 0

    member_status = []

    for user in members:

        trainings = []

        member_completed = 0

        for training in required_trainings:

            status = get_training_status(
                user,
                training,
                year,
                month
            )

            if status["completed"]:
                completed += 1
                member_completed += 1

            trainings.append({
                "training": training,
                "completed": status["completed"],
                "completion": status["completion"]
            })

        member_status.append({
            "user": user,
            "trainings": trainings,
            "completed": member_completed,
            "total": len(required_trainings)
        })

    missing = total_required - completed

    return render_template(
        "training/index.html",
        active="training",
        members=member_status,
        trainings=required_trainings,
        year=year,
        month=month,
        total_required=total_required,
        completed=completed,
        missing=missing
    )


# ==========================================================
# API - ÜBERSICHT
# ==========================================================

@training_bp.route("/status")
def status():

    if not is_admin():
        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    year, month = current_month()

    members = get_active_members()

    trainings = get_required_trainings()

    result = []

    total = 0
    completed = 0

    for user in members:

        user_trainings = []

        for training in trainings:

            completion = get_month_completion(
                user.id,
                training.id,
                year,
                month
            )

            is_completed = completion is not None

            total += 1

            if is_completed:
                completed += 1

            user_trainings.append({
                "id": training.id,
                "name": training.name,
                "completed": is_completed,
                "completed_at": (
                    completion.completed_at.isoformat()
                    if completion and completion.completed_at
                    else None
                ),
                "trainer_name": (
                    completion.trainer_name
                    if completion
                    else None
                )
            })

        result.append({
            "user_id": user.id,
            "username": user.username,
            "trainings": user_trainings
        })

    return jsonify({
        "year": year,
        "month": month,
        "total": total,
        "completed": completed,
        "missing": total - completed,
        "members": result
    })


# ==========================================================
# AUSBILDUNGEN
# ==========================================================

@training_bp.route("/trainings")
def trainings():

    if not is_admin():
        return "Keine Berechtigung", 403

    all_trainings = (
        Training.query
        .order_by(
            Training.active.desc(),
            Training.name.asc()
        )
        .all()
    )

    return render_template(
        "training/trainings.html",
        active="training",
        trainings=all_trainings
    )


# ==========================================================
# AUSBILDUNG ANZEIGEN
# ==========================================================

@training_bp.route(
    "/trainings/<int:training_id>"
)
def training_detail(training_id):

    if not is_admin():
        return "Keine Berechtigung", 403

    training = Training.query.get_or_404(
        training_id
    )

    return render_template(
        "training/training_detail.html",
        active="training",
        training=training
    )


# ==========================================================
# AUSBILDUNG ERSTELLEN
# ==========================================================

@training_bp.route(
    "/trainings/create",
    methods=["GET", "POST"]
)
def create_training():

    if not is_admin():
        return "Keine Berechtigung", 403

    if request.method == "POST":

        name = (
            request.form
            .get("name", "")
            .strip()
        )

        description = (
            request.form
            .get("description", "")
            .strip()
        )

        document = (
            request.form
            .get("document", "")
            .strip()
        )

        required_monthly = (
            request.form
            .get("required_monthly")
            == "on"
        )

        active = (
            request.form
            .get("active")
            == "on"
        )

        if not name:

            flash(
                "Bitte einen Namen für die Ausbildung angeben.",
                "error"
            )

            return render_template(
                "training/training_form.html",
                active="training",
                training=None
            )

        existing = (
            Training.query
            .filter(
                func.lower(
                    Training.name
                ) == name.lower()
            )
            .first()
        )

        if existing:

            flash(
                "Eine Ausbildung mit diesem Namen existiert bereits.",
                "error"
            )

            return render_template(
                "training/training_form.html",
                active="training",
                training=None
            )

        training = Training(
            name=name,
            description=description,
            document=document,
            required_monthly=required_monthly,
            active=active
        )

        db.session.add(training)
        db.session.commit()

        flash(
            f"Ausbildung „{name}“ wurde erstellt.",
            "success"
        )

        return redirect(
            url_for(
                "training.trainings"
            )
        )

    return render_template(
        "training/training_form.html",
        active="training",
        training=None
    )


# ==========================================================
# AUSBILDUNG BEARBEITEN
# ==========================================================

@training_bp.route(
    "/trainings/<int:training_id>/edit",
    methods=["GET", "POST"]
)
def edit_training(training_id):

    if not is_admin():
        return "Keine Berechtigung", 403

    training = Training.query.get_or_404(
        training_id
    )

    if request.method == "POST":

        name = (
            request.form
            .get("name", "")
            .strip()
        )

        description = (
            request.form
            .get("description", "")
            .strip()
        )

        document = (
            request.form
            .get("document", "")
            .strip()
        )

        required_monthly = (
            request.form
            .get("required_monthly")
            == "on"
        )

        active = (
            request.form
            .get("active")
            == "on"
        )

        if not name:

            flash(
                "Der Name darf nicht leer sein.",
                "error"
            )

            return render_template(
                "training/training_form.html",
                active="training",
                training=training
            )

        existing = (
            Training.query
            .filter(
                func.lower(
                    Training.name
                ) == name.lower(),
                Training.id != training.id
            )
            .first()
        )

        if existing:

            flash(
                "Eine andere Ausbildung verwendet bereits diesen Namen.",
                "error"
            )

            return render_template(
                "training/training_form.html",
                active="training",
                training=training
            )

        training.name = name
        training.description = description
        training.document = document
        training.required_monthly = required_monthly
        training.active = active
        training.updated_at = datetime.utcnow()

        db.session.commit()

        flash(
            f"Ausbildung „{name}“ wurde aktualisiert.",
            "success"
        )

        return redirect(
            url_for(
                "training.training_detail",
                training_id=training.id
            )
        )

    return render_template(
        "training/training_form.html",
        active="training",
        training=training
    )


# ==========================================================
# AUSBILDUNG LÖSCHEN
# ==========================================================

@training_bp.route(
    "/trainings/<int:training_id>/delete",
    methods=["POST"]
)
def delete_training(training_id):

    if not is_admin():
        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    training = Training.query.get_or_404(
        training_id
    )

    name = training.name

    try:

        db.session.delete(training)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": (
                f"Ausbildung „{name}“ wurde gelöscht."
            )
        })

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": (
                f"Fehler beim Löschen: {e}"
            )
        }), 500


# ==========================================================
# MITGLIEDER
# ==========================================================

@training_bp.route("/members")
def members():

    if not is_admin():
        return "Keine Berechtigung", 403

    year, month = current_month()

    all_members = get_active_members()

    trainings = get_required_trainings()

    member_data = []

    for user in all_members:

        completed_count = 0
        training_data = []

        for training in trainings:

            completion = get_month_completion(
                user.id,
                training.id,
                year,
                month
            )

            is_completed = completion is not None

            if is_completed:
                completed_count += 1

            training_data.append({
                "training": training,
                "completed": is_completed,
                "completion": completion
            })

        member_data.append({
            "user": user,
            "trainings": training_data,
            "completed": completed_count,
            "total": len(trainings)
        })

    return render_template(
        "training/members.html",
        active="training",
        members=member_data,
        trainings=trainings,
        year=year,
        month=month
    )


# ==========================================================
# MITGLIED DETAIL
# ==========================================================

@training_bp.route(
    "/member/<int:user_id>"
)
def member_detail(user_id):

    if not is_admin():
        return "Keine Berechtigung", 403

    user = UserProfile.query.get_or_404(
        user_id
    )

    trainings = (
        Training.query
        .filter_by(active=True)
        .order_by(
            Training.name.asc()
        )
        .all()
    )

    completions = (
        TrainingCompletion.query
        .filter_by(
            user_id=user.id
        )
        .order_by(
            TrainingCompletion.completed_at.desc()
        )
        .all()
    )

    return render_template(
        "training/member_detail.html",
        active="training",
        user=user,
        trainings=trainings,
        completions=completions
    )


# ==========================================================
# AUSBILDUNG ABSCHLIESSEN
# ==========================================================

@training_bp.route(
    "/complete",
    methods=["POST"]
)
def complete_training():

    if not is_admin():
        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    data = request.get_json(
        silent=True
    )

    if data is None:
        data = request.form

    user_id = data.get("user_id")
    training_id = data.get("training_id")


    if not user_id or not training_id:

        return jsonify({
            "success": False,
            "message": (
                "Mitglied oder Ausbildung fehlt."
            )
        }), 400

    try:

        user_id = int(user_id)
        training_id = int(training_id)

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "success": False,
            "message": (
                "Ungültige Mitglieds- oder Ausbildungs-ID."
            )
        }), 400

    # ======================================================
    # BENUTZER ÜBER INTERNE DB-ID SUCHEN
    # ======================================================

    user = db.session.get(
        UserProfile,
        user_id
    )

    if not user:

        return jsonify({
            "success": False,
            "message": (
                f"Mitglied mit der Datenbank-ID "
                f"{user_id} wurde nicht gefunden."
            )
        }), 404

    # ======================================================
    # AUSBILDUNG SUCHEN
    # ======================================================

    training = db.session.get(
        Training,
        training_id
    )

    if not training or not training.active:

        return jsonify({
            "success": False,
            "message": "Ausbildung wurde nicht gefunden."
        }), 404

    # ======================================================
    # AKTUELLEN MONAT PRÜFEN
    # ======================================================

    year, month = current_month()

    existing = get_month_completion(
        user.id,
        training.id,
        year,
        month
    )

    if existing:

        return jsonify({
            "success": False,
            "message": (
                "Diese Ausbildung wurde für "
                "diesen Monat bereits eingetragen."
            ),
            "completed": True,
            "completion_id": existing.id
        }), 409

    # ======================================================
    # TRAINER
    # ======================================================

    user_data = session.get("user", {})
    trainer_id = user_data.get("id")


    trainer_name = (
        user_data.get("username")
        or "Unbekannt"
    )

    note = data.get(
        "note",
        ""
    )

    # ======================================================
    # ABSCHLUSS ERSTELLEN
    # ======================================================

    completion = TrainingCompletion(
        user_id=user.id,
        training_id=training.id,
        year=year,
        month=month,
        completed_at=datetime.utcnow(),
        trainer_id=trainer_id,
        trainer_name=trainer_name,
        note=str(note).strip()
    )

    try:

        db.session.add(completion)
        db.session.commit()

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": (
                f"Fehler beim Speichern: {e}"
            )
        }), 500

    return jsonify({
        "success": True,
        "message": (
            f"{training.name} für "
            f"{user.username} wurde eingetragen."
        ),
        "completed": True,
        "completion_id": completion.id,
        "training": training.name,
        "username": user.username,
        "user_id": user.id,
        "year": year,
        "month": month,
        "completed_at": (
            completion.completed_at.isoformat()
        ),
        "trainer_name": trainer_name
    })


# ==========================================================
# AUSBILDUNG ZURÜCKNEHMEN
# ==========================================================

@training_bp.route(
    "/completion/<int:completion_id>/delete",
    methods=["POST"]
)
def delete_completion(completion_id):

    if not is_admin():
        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    completion = TrainingCompletion.query.get_or_404(
        completion_id
    )

    try:

        db.session.delete(completion)
        db.session.commit()

        return jsonify({
            "success": True,
            "message": (
                "Ausbildungseintrag wurde entfernt."
            )
        })

    except Exception as e:

        db.session.rollback()

        return jsonify({
            "success": False,
            "message": (
                f"Fehler beim Entfernen: {e}"
            )
        }), 500


# ==========================================================
# MITGLIED - AUSBILDUNGSSTATUS API
# ==========================================================

@training_bp.route(
    "/member/<int:user_id>/status"
)
def member_status(user_id):

    if not is_admin():
        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    user = db.session.get(
        UserProfile,
        user_id
    )

    if not user:

        return jsonify({
            "error": "Mitglied wurde nicht gefunden."
        }), 404

    year, month = current_month()

    trainings = (
        Training.query
        .filter_by(active=True)
        .order_by(
            Training.name.asc()
        )
        .all()
    )

    result = []

    for training in trainings:

        completion = get_month_completion(
            user.id,
            training.id,
            year,
            month
        )

        result.append({
            "training_id": training.id,
            "training": training.name,
            "required_monthly": training.required_monthly,
            "completed": completion is not None,
            "completion_id": (
                completion.id
                if completion
                else None
            ),
            "completed_at": (
                completion.completed_at.isoformat()
                if completion and completion.completed_at
                else None
            ),
            "trainer_name": (
                completion.trainer_name
                if completion
                else None
            )
        })

    return jsonify({
        "user_id": user.id,
        "username": user.username,
        "year": year,
        "month": month,
        "trainings": result
    })


# ==========================================================
# API - AUSBILDUNGEN
# ==========================================================

@training_bp.route(
    "/api/trainings"
)
def api_trainings():

    if not is_admin():
        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    trainings = (
        Training.query
        .order_by(
            Training.name.asc()
        )
        .all()
    )

    return jsonify([
        {
            "id": training.id,
            "name": training.name,
            "description": training.description,
            "document": training.document,
            "required_monthly": training.required_monthly,
            "active": training.active
        }
        for training in trainings
    ])

