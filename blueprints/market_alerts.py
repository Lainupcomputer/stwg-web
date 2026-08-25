from datetime import datetime

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    session,
)

from database import db
from database.models import (
    MarketAlert,
    MarketItem,
    MarketPriceHistory,
)


# ==========================================================
# MARKET ALERT BLUEPRINT
# ==========================================================

def market_alert_blueprint() -> Blueprint:

    alerts = Blueprint(
        "market_alerts",
        __name__,
        url_prefix="/market/alerts",
    )

    # ======================================================
    # HELPERS
    # ======================================================

    def get_user_id():
        """
        Holt die Discord User-ID aus der Session.
        """

        user = session.get("user")

        if not user:
            return None

        return str(
            user.get("id")
        )

    # ======================================================
    # CURRENT PRICE
    # ======================================================

    def get_current_price(item):
        """
        Holt den zuletzt gespeicherten Marktpreis.

        Falls noch keine Historie existiert,
        wird der Base-Preis verwendet.
        """

        latest = (
            MarketPriceHistory.query
            .filter_by(
                item_id=item.id
            )
            .order_by(
                MarketPriceHistory.timestamp.desc()
            )
            .first()
        )

        if latest:
            return float(
                latest.price
            )

        return float(
            item.base_price
        )

    # ======================================================
    # SERIALIZE ALERT
    # ======================================================

    def serialize_alert(alert):

        item = alert.item

        current_price = get_current_price(
            item
        )

        return {
            "id": alert.id,

            "item_id": item.id,

            "item_name":
                item.name,

            "display_name":
                item.display_name,

            "external_id":
                item.external_id,

            "condition":
                alert.condition,

            "target_price":
                float(
                    alert.target_price
                ),

            "current_price":
                current_price,

            "enabled":
                alert.enabled,

            "armed":
                alert.armed,

            "created_at":
                (
                    alert.created_at.isoformat()
                    if alert.created_at
                    else None
                ),
        }

    # ======================================================
    # PAGE
    # ======================================================

    @alerts.route("/")
    def index():

        user_id = get_user_id()

        if not user_id:
            return (
                "Nicht eingeloggt",
                401
            )

        user_alerts = (
            MarketAlert.query
            .filter_by(
                user_id=user_id
            )
            .order_by(
                MarketAlert.created_at.desc()
            )
            .all()
        )

        items = (
            MarketItem.query
            .filter_by(
                enabled=True
            )
            .order_by(
                MarketItem.display_name.asc()
            )
            .all()
        )

        return render_template(
            "market/alerts.html",
            alerts=user_alerts,
            items=items,
            active="market_alerts",
        )

    # ======================================================
    # GET ALERTS
    # ======================================================

    @alerts.route(
        "/api",
        methods=["GET"]
    )
    def get_alerts():

        user_id = get_user_id()

        if not user_id:
            return jsonify({
                "error":
                    "Nicht eingeloggt"
            }), 401

        user_alerts = (
            MarketAlert.query
            .filter_by(
                user_id=user_id
            )
            .order_by(
                MarketAlert.created_at.desc()
            )
            .all()
        )

        return jsonify({
            "alerts": [
                serialize_alert(alert)
                for alert in user_alerts
            ]
        })

    # ======================================================
    # CREATE ALERT
    # ======================================================

    @alerts.route(
        "/api",
        methods=["POST"]
    )
    def create_alert():

        user_id = get_user_id()

        if not user_id:
            return jsonify({
                "error":
                    "Nicht eingeloggt"
            }), 401

        data = request.get_json(
            silent=True
        )

        if not data:
            return jsonify({
                "error":
                    "Keine JSON-Daten"
            }), 400

        # --------------------------------------------------
        # ITEM
        # --------------------------------------------------

        try:
            item_id = int(
                data.get("item_id")
            )
        except (
            TypeError,
            ValueError
        ):
            return jsonify({
                "error":
                    "Ungültiges Marktitem"
            }), 400

        item = db.session.get(
            MarketItem,
            item_id
        )

        if not item:
            return jsonify({
                "error":
                    "Marktitem nicht gefunden"
            }), 404

        if not item.enabled:
            return jsonify({
                "error":
                    "Dieses Marktitem ist deaktiviert"
            }), 400

        # --------------------------------------------------
        # CONDITION
        # --------------------------------------------------

        condition = str(
            data.get(
                "condition",
                ""
            )
        ).strip()

        if condition not in (
            "<",
            ">"
        ):
            return jsonify({
                "error":
                    "Bedingung muss < oder > sein"
            }), 400

        # --------------------------------------------------
        # TARGET PRICE
        # --------------------------------------------------

        try:
            target_price = float(
                data.get(
                    "target_price"
                )
            )
        except (
            TypeError,
            ValueError
        ):
            return jsonify({
                "error":
                    "Ungültiger Grenzpreis"
            }), 400

        if target_price < 0:
            return jsonify({
                "error":
                    "Grenzpreis darf nicht negativ sein"
            }), 400

        # --------------------------------------------------
        # DUPLICATE CHECK
        # --------------------------------------------------

        existing = (
            MarketAlert.query
            .filter_by(
                user_id=user_id,
                item_id=item.id,
                condition=condition,
                target_price=target_price,
            )
            .first()
        )

        if existing:
            return jsonify({
                "error":
                    "Dieser Alarm existiert bereits"
            }), 409

        # --------------------------------------------------
        # CURRENT PRICE
        # --------------------------------------------------

        current_price = get_current_price(
            item
        )

        # --------------------------------------------------
        # INITIAL ARMED STATE
        #
        # Wenn der Preis bereits über/unter
        # dem Grenzwert liegt, darf NICHT
        # sofort ein Alarm ausgelöst werden.
        #
        # Der Alarm wartet zunächst darauf,
        # dass der Preis wieder auf die andere
        # Seite der Grenze kommt.
        # --------------------------------------------------

        if condition == "<":

            armed = (
                current_price >= target_price
            )

        else:

            armed = (
                current_price <= target_price
            )

        alert = MarketAlert(
            user_id=user_id,
            item_id=item.id,
            condition=condition,
            target_price=target_price,
            enabled=True,
            armed=armed,
            last_price=current_price,
            created_at=datetime.utcnow(),
        )

        db.session.add(
            alert
        )

        db.session.commit()

        return jsonify({
            "success": True,
            "alert":
                serialize_alert(
                    alert
                ),
        }), 201

    # ======================================================
    # UPDATE ALERT
    # ======================================================

    @alerts.route(
        "/api/<int:alert_id>",
        methods=["PUT"]
    )
    def update_alert(alert_id):

        user_id = get_user_id()

        if not user_id:
            return jsonify({
                "error":
                    "Nicht eingeloggt"
            }), 401

        alert = db.session.get(
            MarketAlert,
            alert_id
        )

        if not alert:
            return jsonify({
                "error":
                    "Alarm nicht gefunden"
            }), 404

        if str(
            alert.user_id
        ) != str(user_id):

            return jsonify({
                "error":
                    "Keine Berechtigung"
            }), 403

        data = request.get_json(
            silent=True
        )

        if not data:
            return jsonify({
                "error":
                    "Keine JSON-Daten"
            }), 400

        # --------------------------------------------------
        # ENABLED
        # --------------------------------------------------

        if "enabled" in data:

            alert.enabled = bool(
                data["enabled"]
            )

        # --------------------------------------------------
        # CONDITION
        # --------------------------------------------------

        if "condition" in data:

            condition = str(
                data["condition"]
            ).strip()

            if condition not in (
                "<",
                ">"
            ):
                return jsonify({
                    "error":
                        "Bedingung muss < oder > sein"
                }), 400

            alert.condition = condition

        # --------------------------------------------------
        # TARGET PRICE
        # --------------------------------------------------

        if "target_price" in data:

            try:
                target_price = float(
                    data["target_price"]
                )
            except (
                TypeError,
                ValueError
            ):
                return jsonify({
                    "error":
                        "Ungültiger Grenzpreis"
                }), 400

            if target_price < 0:
                return jsonify({
                    "error":
                        "Grenzpreis darf nicht negativ sein"
                }), 400

            alert.target_price = target_price

        # --------------------------------------------------
        # ALARM NEU ARMEN
        #
        # Bei Änderung der Bedingungen beginnen
        # wir wieder mit einem sauberen Zustand.
        # --------------------------------------------------

        current_price = get_current_price(
            alert.item
        )

        if alert.condition == "<":

            alert.armed = (
                current_price >=
                alert.target_price
            )

        else:

            alert.armed = (
                current_price <=
                alert.target_price
            )

        alert.last_price = current_price

        db.session.commit()

        return jsonify({
            "success": True,
            "alert":
                serialize_alert(
                    alert
                ),
        })

    # ======================================================
    # TOGGLE ALERT
    # ======================================================

    @alerts.route(
        "/api/<int:alert_id>/toggle",
        methods=["POST"]
    )
    def toggle_alert(alert_id):

        user_id = get_user_id()

        if not user_id:
            return jsonify({
                "error":
                    "Nicht eingeloggt"
            }), 401

        alert = db.session.get(
            MarketAlert,
            alert_id
        )

        if not alert:
            return jsonify({
                "error":
                    "Alarm nicht gefunden"
            }), 404

        if str(
            alert.user_id
        ) != str(user_id):

            return jsonify({
                "error":
                    "Keine Berechtigung"
            }), 403

        alert.enabled = not alert.enabled

        # Beim erneuten Aktivieren sauber
        # neu scharfstellen.
        if alert.enabled:

            current_price = get_current_price(
                alert.item
            )

            if alert.condition == "<":

                alert.armed = (
                    current_price >=
                    alert.target_price
                )

            else:

                alert.armed = (
                    current_price <=
                    alert.target_price
                )

            alert.last_price = current_price

        db.session.commit()

        return jsonify({
            "success": True,
            "enabled":
                alert.enabled,
        })

    # ======================================================
    # DELETE ALERT
    # ======================================================

    @alerts.route(
        "/api/<int:alert_id>",
        methods=["DELETE"]
    )
    def delete_alert(alert_id):

        user_id = get_user_id()

        if not user_id:
            return jsonify({
                "error":
                    "Nicht eingeloggt"
            }), 401

        alert = db.session.get(
            MarketAlert,
            alert_id
        )

        if not alert:
            return jsonify({
                "error":
                    "Alarm nicht gefunden"
            }), 404

        if str(
            alert.user_id
        ) != str(user_id):

            return jsonify({
                "error":
                    "Keine Berechtigung"
            }), 403

        db.session.delete(
            alert
        )

        db.session.commit()

        return jsonify({
            "success": True
        })

    return alerts