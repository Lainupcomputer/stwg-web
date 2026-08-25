from functools import wraps
from flask import session, redirect, url_for, jsonify
import json


def require_role_management(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("can_manage_roles"):
            # Optional: Wenn du lieber JSON zurückgeben willst:
            # return jsonify({"error": "Nicht autorisiert"}), 403
            return redirect(url_for("index"))
        return fn(*args, **kwargs)
    return wrapper


def has_license(user, license_name):
    if not user or not user.licenses:
        return False

    try:
        licenses = json.loads(user.licenses)

        return any(
            license_data.get("name") == license_name
            and license_data.get("has") is True
            for license_data in licenses
        )

    except (json.JSONDecodeError, TypeError):
        return False
    

def require_admin_permission(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin", False):

            # return jsonify({"error": "Nicht autorisiert"}), 403
            return redirect(url_for("index"))
        return fn(*args, **kwargs)
    return wrapper

