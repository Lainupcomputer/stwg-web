from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    session
)

from database import db
from database.models import UserProfile, ActionQueue

import json


license_management = Blueprint(
    "license_management",
    __name__,
    url_prefix="/license-management"
)


# ==========================================================
# KONFIGURATION
# ==========================================================

DEFAULT_LICENSES = [
    {
        "name": "Flugausbildung",
        "description": "Die Flugprüfung bestanden."
    },
    {
        "name": "Leitung",
        "description": "Mitglied der Leitung sein."
    },
    {
        "name": "Supporter",
        "description": "Tickets bearbeiten"
    },
    {
        "name": "Zustechen",
        "description": "Zustechen"
    },
    {
        "name": "Ausbilder",
        "description": "Ausbilder sein"
    },
    {
        "name": "Mitglied",
        "description": "Mitglied sein"
    }
]


# ==========================================================
# BERECHTIGUNG
# ==========================================================

def has_management_permission():

    return bool(
        session.get("is_admin")
    )


# ==========================================================
# LIZENZEN AUS JSON LESEN
# ==========================================================

def get_user_licenses(user):

    if not user.licenses:
        return []

    try:

        licenses = json.loads(
            user.licenses
        )

        if not isinstance(
            licenses,
            list
        ):
            return []

        return licenses

    except (
        json.JSONDecodeError,
        TypeError
    ):



        return []


# ==========================================================
# LIZENZ STATUS
# ==========================================================

def user_has_license(
    user,
    license_name
):

    licenses = get_user_licenses(
        user
    )

    for license_data in licenses:

        if (
            license_data.get("name")
            == license_name
        ):

            return bool(
                license_data.get("has")
            )

    return False


# ==========================================================
# LIZENZ SETZEN
# ==========================================================

def set_user_license(
    user,
    license_name,
    enabled,
    description=""
):

    licenses = get_user_licenses(
        user
    )

    found = False

    for license_data in licenses:

        if (
            license_data.get("name")
            == license_name
        ):

            license_data["has"] = enabled

            if description:
                license_data["description"] = description

            found = True

            break

    if not found:

        licenses.append(
            {
                "name": license_name,
                "has": enabled,
                "description": description
            }
        )

    user.licenses = json.dumps(
        licenses,
        ensure_ascii=False
    )


# ==========================================================
# ALLE LIZENZNAMEN SAMMELN
# ==========================================================

def get_all_license_names(users):

    license_map = {}

    # Standard-Lizenzen
    for license_data in DEFAULT_LICENSES:

        name = license_data["name"]

        license_map[name] = {
            "name": name,
            "description":
                license_data["description"]
        }

    # Zusätzlich alle Lizenzen aus
    # den vorhandenen User-Profilen
    for user in users:

        licenses = get_user_licenses(
            user
        )

        for license_data in licenses:

            name = license_data.get(
                "name"
            )

            if not name:
                continue

            if name not in license_map:

                license_map[name] = {
                    "name": name,
                    "description":
                        license_data.get(
                            "description",
                            ""
                        )
                }

    return list(
        license_map.values()
    )


# ==========================================================
# ÜBERSICHT
# ==========================================================

@license_management.route("/")
def index():

    if not has_management_permission():

        return (
            "Keine Berechtigung",
            403
        )

    users = (
        UserProfile.query
        .order_by(
            UserProfile.username.asc()
        )
        .all()
    )

    licenses = get_all_license_names(
        users
    )

    user_data = []

    for user in users:

        user_licenses = {}

        for license_data in get_user_licenses(
            user
        ):

            name = license_data.get(
                "name"
            )

            if name:

                user_licenses[name] = bool(
                    license_data.get(
                        "has",
                        False
                    )
                )

        user_data.append(
            {
                "id": user.id,
                "user_id": user.user_id,
                "username": user.username,
                "licenses": user_licenses
            }
        )

    return render_template(
        "license_management.html",
        users=user_data,
        licenses=licenses,
        active="license_management"
    )


# ==========================================================
# LIZENZ ÄNDERN
# ==========================================================

@license_management.route(
    "/set",
    methods=["POST"]
)
def set_license():

    if not has_management_permission():

        return jsonify(
            {
                "error":
                    "Keine Berechtigung"
            }
        ), 403

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify(
            {
                "error":
                    "Keine Daten empfangen"
            }
        ), 400

    try:

        user_id = int(
            data.get("user_id")
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify(
            {
                "error":
                    "Ungültige Benutzer-ID"
            }
        ), 400

    license_name = (
        data.get("license")
    )

    enabled = data.get(
        "enabled"
    )

    if not license_name:

        return jsonify(
            {
                "error":
                    "Keine Lizenz angegeben"
            }
        ), 400

    if not isinstance(
        enabled,
        bool
    ):

        return jsonify(
            {
                "error":
                    "Ungültiger Status"
            }
        ), 400

    user = (
        UserProfile.query
        .filter_by(id=user_id)
        .first()
    )

    if not user:

        return jsonify(
            {
                "error":
                    "Benutzer nicht gefunden"
            }
        ), 404

    # Beschreibung aus bestehender Lizenz
    description = ""

    for license_data in get_user_licenses(
        user
    ):

        if (
            license_data.get("name")
            == license_name
        ):

            description = license_data.get(
                "description",
                ""
            )

            break

    # Falls es eine Standard-Lizenz ist
    if not description:

        for license_data in DEFAULT_LICENSES:

            if (
                license_data["name"]
                == license_name
            ):

                description = (
                    license_data["description"]
                )

                break

    set_user_license(
        user=user,
        license_name=license_name,
        enabled=enabled,
        description=description
    )

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()



        return jsonify(
            {
                "error":
                    "Datenbankfehler"
            }
        ), 500


    if enabled:
        text = (
            f"🎓 Dir wurde die Lizenz **{license_name}** "
            f"erteilt."
        )

    else:
        text = (
            f"🎓 Dir wurde die Lizenz **{license_name}** "
            f"entzogen."
        )

    action = ActionQueue(
        key="send_user_message",
        data={"userId": user.user_id, "text": text}
    )
    db.session.add(action)
    db.session.commit()


    return jsonify(
        {
            "status": "ok",
            "user_id": user.id,
            "username": user.username,
            "license": license_name,
            "enabled": enabled
        }
    )
