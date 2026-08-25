from flask import (
    Blueprint,
    jsonify,
    render_template,
    session
)
import subprocess

SERVICE_NAME = "stwg-discord-bot.service"
LOG_LINES = 100

bot_control_bp = Blueprint(
    "bot_control",
    __name__,
    url_prefix="/bot"
)

def is_admin():
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


@bot_control_bp.route("/")
def index():

    if not is_admin():

        return "Keine Berechtigung", 403

    return render_template(
        "control/bot.html",
        active="bot"
    )


@bot_control_bp.route("/status")
def status():

    if not is_admin():

        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    service = get_service_status()
    details = get_service_details()

    return jsonify({
        "running": service["running"],
        "active": service["active"],
        "enabled": service["enabled"],
        "service": SERVICE_NAME,
        "details": details
    })


@bot_control_bp.route("/output")
def output():

    if not is_admin():

        return jsonify({
            "error": "Keine Berechtigung"
        }), 403

    success, output_text = get_output(
        LOG_LINES
    )

    return jsonify({
        "success": success,
        "running": get_service_status()["running"],
        "output": output_text
    })


@bot_control_bp.route(
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


@bot_control_bp.route(
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


@bot_control_bp.route(
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


@bot_control_bp.route(
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


@bot_control_bp.route(
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