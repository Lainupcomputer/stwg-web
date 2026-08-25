from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    session
)

import subprocess


# ==========================================================
# KONFIGURATION
# ==========================================================

SERVICE_NAME = "stwg-market-grabber.service"

LOG_LINES = 100

INTERVAL_KEY = "ucpp.poll_intervall"


# ==========================================================
# BLUEPRINT
# ==========================================================

grabber_control_bp = Blueprint(
    "grabber_control",
    __name__,
    url_prefix="/grabber"
)


# ==========================================================
# HILFSFUNKTIONEN
# ==========================================================

def is_admin():
    """
    Prüft, ob der aktuelle Benutzer Admin-Rechte besitzt.
    """

    return session.get(
        "is_supporter",
        False
    )


def run_systemctl(
    command,
    timeout=15
):
    """
    Führt einen systemctl-Befehl aus.

    Rückgabe:
        success, message
    """

    try:

        result = subprocess.run(
            [
                "systemctl",
                command,
                SERVICE_NAME
            ],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode == 0:

            return (
                True,
                result.stdout.strip()
                or f"systemctl {command} erfolgreich."
            )

        return (
            False,
            result.stderr.strip()
            or f"systemctl {command} fehlgeschlagen."
        )

    except subprocess.TimeoutExpired:

        return (
            False,
            f"Timeout bei systemctl {command}."
        )

    except Exception as e:

        return (
            False,
            f"Fehler bei systemctl {command}: {e}"
        )


def get_service_status():
    """
    Liest den aktuellen systemd-Status.
    """

    try:

        active = subprocess.run(
            [
                "systemctl",
                "is-active",
                SERVICE_NAME
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        enabled = subprocess.run(
            [
                "systemctl",
                "is-enabled",
                SERVICE_NAME
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        active_state = active.stdout.strip()

        enabled_state = enabled.stdout.strip()

        return {
            "running": active_state == "active",
            "active": active_state,
            "enabled": enabled_state
        }

    except Exception as e:

        return {
            "running": False,
            "active": "unknown",
            "enabled": "unknown",
            "error": str(e)
        }


def get_service_details():
    """
    Liest zusätzliche Informationen aus systemd.
    """

    properties = [
        "ActiveState",
        "SubState",
        "MainPID",
        "ExecMainStartTimestamp",
        "MemoryCurrent",
        "CPUUsageNSec",
        "NRestarts"
    ]

    try:

        result = subprocess.run(
            [
                "systemctl",
                "show",
                SERVICE_NAME,
                "--no-pager",
                *[
                    f"--property={property_name}"
                    for property_name in properties
                ]
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:

            return {
                "error": result.stderr.strip()
            }

        data = {}

        for line in result.stdout.splitlines():

            if "=" not in line:
                continue

            key, value = line.split(
                "=",
                1
            )

            data[key] = value

        return data

    except Exception as e:

        return {
            "error": str(e)
        }


def get_output(
    lines=LOG_LINES
):
    """
    Liest die letzten Grabber-Logs aus journalctl.
    """

    try:

        result = subprocess.run(
            [
                "journalctl",
                "-u",
                SERVICE_NAME,
                "-n",
                str(lines),
                "--no-pager",
                "-o",
                "cat"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:

            return (
                False,
                result.stderr.strip()
            )

        return (
            True,
            result.stdout
        )

    except Exception as e:

        return (
            False,
            f"Fehler beim Lesen der Logs: {e}"
        )


def get_storage_value(
    key,
    default=None
):
    """
    Liest einen Wert aus DataStorage.
    """

    try:

        # Import bewusst hier, damit der Blueprint
        # unabhängig geladen werden kann.
        from database.models import DataStorage

        entry = (
            DataStorage.query
            .filter_by(key=key)
            .first()
        )

        if entry is None:

            return default

        return entry.data

    except Exception:

        return default


def set_storage_value(
    key,
    value
):
    """
    Erstellt oder aktualisiert einen DataStorage-Eintrag.
    """

    from database import db
    from database.models import DataStorage

    entry = (
        DataStorage.query
        .filter_by(key=key)
        .first()
    )

    if entry is None:

        entry = DataStorage(
            key=key,
            data=str(value)
        )

        db.session.add(entry)

    else:

        entry.data = str(value)

    db.session.commit()


# ==========================================================
# SEITE
# ==========================================================

@grabber_control_bp.route("/")
def index():

    if not is_admin():

        return "Keine Berechtigung", 403

    return render_template(
        "control/markt_grabber.html",
        active="grabber"
    )


# ==========================================================
# STATUS
# ==========================================================

@grabber_control_bp.route("/status")
def status():

    if not is_admin():

        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    service = get_service_status()

    details = get_service_details()

    interval = get_storage_value(
        INTERVAL_KEY,
        "300"
    )

    return jsonify({
        "running": service["running"],
        "active": service["active"],
        "enabled": service["enabled"],
        "service": SERVICE_NAME,
        "interval": interval,
        "details": details
    })


# ==========================================================
# OUTPUT
# ==========================================================

@grabber_control_bp.route("/output")
def output():

    if not is_admin():

        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    lines = request.args.get(
        "lines",
        LOG_LINES,
        type=int
    )

    if lines < 1:
        lines = 1

    if lines > 500:
        lines = 500

    success, output_text = get_output(
        lines
    )

    return jsonify({
        "success": success,
        "running": get_service_status()["running"],
        "output": output_text
    })


# ==========================================================
# START
# ==========================================================

@grabber_control_bp.route(
    "/start",
    methods=["POST"]
)
def start():

    if not is_admin():

        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    success, message = run_systemctl(
        "start"
    )

    service = get_service_status()

    return jsonify({
        "success": success,
        "message": message,
        "running": service["running"],
        "active": service["active"]
    })


# ==========================================================
# STOP
# ==========================================================

@grabber_control_bp.route(
    "/stop",
    methods=["POST"]
)
def stop():

    if not is_admin():

        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    success, message = run_systemctl(
        "stop"
    )

    service = get_service_status()

    return jsonify({
        "success": success,
        "message": message,
        "running": service["running"],
        "active": service["active"]
    })


# ==========================================================
# RESTART
# ==========================================================

@grabber_control_bp.route(
    "/restart",
    methods=["POST"]
)
def restart():

    if not is_admin():

        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    success, message = run_systemctl(
        "restart"
    )

    service = get_service_status()

    return jsonify({
        "success": success,
        "message": message,
        "running": service["running"],
        "active": service["active"]
    })


# ==========================================================
# ENABLE
# ==========================================================

@grabber_control_bp.route(
    "/enable",
    methods=["POST"]
)
def enable():

    if not is_admin():

        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    success, message = run_systemctl(
        "enable"
    )

    service = get_service_status()

    return jsonify({
        "success": success,
        "message": message,
        "enabled": service["enabled"]
    })


# ==========================================================
# DISABLE
# ==========================================================

@grabber_control_bp.route(
    "/disable",
    methods=["POST"]
)
def disable():

    if not is_admin():

        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    success, message = run_systemctl(
        "disable"
    )

    service = get_service_status()

    return jsonify({
        "success": success,
        "message": message,
        "enabled": service["enabled"]
    })


# ==========================================================
# CONFIG
# ==========================================================

@grabber_control_bp.route("/config")
def config():

    if not is_admin():

        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    interval = get_storage_value(
        INTERVAL_KEY,
        "300"
    )

    return jsonify({
        "interval": interval
    })


# ==========================================================
# CONFIG SPEICHERN
# ==========================================================

@grabber_control_bp.route(
    "/config",
    methods=["POST"]
)
def update_config():

    if not is_admin():

        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    data = request.get_json(
        silent=True
    ) or {}

    interval = data.get(
        "interval"
    )

    if interval is None:

        return jsonify({
            "success": False,
            "message": "Intervall fehlt."
        }), 400

    try:

        interval = int(
            interval
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({
            "success": False,
            "message": "Intervall muss eine Zahl sein."
        }), 400

    if interval < 10:

        return jsonify({
            "success": False,
            "message": (
                "Das Intervall muss mindestens "
                "10 Sekunden betragen."
            )
        }), 400

    if interval > 86400:

        return jsonify({
            "success": False,
            "message": (
                "Das Intervall darf maximal "
                "86400 Sekunden betragen."
            )
        }), 400

    try:

        set_storage_value(
            INTERVAL_KEY,
            interval
        )

    except Exception as e:

        return jsonify({
            "success": False,
            "message": (
                f"Fehler beim Speichern: {e}"
            )
        }), 500

    return jsonify({
        "success": True,
        "message": (
            f"Intervall auf {interval} Sekunden gesetzt."
        ),
        "interval": interval
    })