from datetime import datetime, timedelta

from flask import (
    Blueprint,
    jsonify,
    render_template,
    request,
    session,
)

from sqlalchemy import desc

from database import db
from database.models import MarketPriceHistory, MarketItem


# ==========================================================
# MARKET BLUEPRINT
# ==========================================================

def market_blueprint() -> Blueprint:

    market = Blueprint(
        "market",
        __name__,
        url_prefix="/market",
    )

    # ======================================================
    # HELPERS
    # ======================================================

    def is_admin():
        return session.get(
            "can_manage_roles",
            False
        )

    # ======================================================
    # SERIALIZE ITEM
    # ======================================================

    def serialize_item(item):

        latest = (
            MarketPriceHistory.query
            .filter_by(
                item_id=item.id
            )
            .order_by(
                desc(
                    MarketPriceHistory.timestamp
                )
            )
            .first()
        )

        return {
            "id": item.id,

            "external_id": item.external_id,

            "name": item.name,

            "display_name":
                item.display_name,

            "min_price":
                float(item.min_price),

            "base_price":
                float(item.base_price),

            "max_price":
                float(item.max_price),

            "enabled":
                item.enabled,

            "current_price": (
                float(latest.price)
                if latest
                else float(item.base_price)
            ),
        }

    # ======================================================
    # MARKET PAGE
    # ======================================================

    @market.route("/")
    def index():

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
            "market/index.html",
            items=items,
            acive="market"
        )

    # ======================================================
    # GRAPH DATA
    # ======================================================

    @market.route(
        "/api/<int:item_id>"
    )
    def graph_data(item_id):

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
                    "Marktitem ist deaktiviert"
            }), 403

        # --------------------------------------------------
        # Zeitraum
        # --------------------------------------------------

        period = request.args.get(
            "period",
            "24h"
        )

        now = datetime.utcnow()

        periods = {
            "1h":
                timedelta(hours=1),

            "6h":
                timedelta(hours=6),

            "24h":
                timedelta(hours=24),

            "7d":
                timedelta(days=7),

            "30d":
                timedelta(days=30),
        }

        since = (
            now
            - periods.get(
                period,
                timedelta(hours=24)
            )
        )

        # --------------------------------------------------
        # Historie
        # --------------------------------------------------

        history = (
            MarketPriceHistory.query
            .filter(
                MarketPriceHistory.item_id
                == item.id,

                MarketPriceHistory.timestamp
                >= since,
            )
            .order_by(
                MarketPriceHistory.timestamp.asc()
            )
            .all()
        )

        labels = [
            entry.timestamp.isoformat()
            for entry in history
        ]

        prices = [
            float(entry.price)
            for entry in history
        ]

        # --------------------------------------------------
        # Aktueller Preis
        # --------------------------------------------------

        current_price = (
            prices[-1]
            if prices
            else float(item.base_price)
        )

        # --------------------------------------------------
        # Response
        # --------------------------------------------------

        return jsonify({

            "item": {

                "id":
                    item.id,

                "external_id":
                    item.external_id,

                "name":
                    item.name,

                "display_name":
                    item.display_name,
            },

            "current_price":
                current_price,

            "min_price":
                float(item.min_price),

            "base_price":
                float(item.base_price),

            "max_price":
                float(item.max_price),

            "labels":
                labels,

            "prices":
                prices,
        })

    # ======================================================
    # MARKET IMPORT
    # ======================================================

    @market.route(
        "/api/import",
        methods=["POST"]
    )
    def import_market_data():

        """
        Nimmt die kompletten Daten des externen
        Markt-Grabbers entgegen.

        Erwartet beispielsweise:

        {
            "items": [
                {
                    "name": "Apfel",
                    "price": 150,
                    "diff": -6.25,
                    "id": 8500
                }
            ]
        }

        Es werden ausschließlich Items gespeichert,
        die in MarketItem existieren UND aktiviert sind.

        Nicht vorhandene oder deaktivierte Items
        werden ignoriert.
        """

        data = request.get_json(
            silent=True
        )

        if not data:
            return jsonify({
                "error":
                    "Keine JSON-Daten erhalten"
            }), 400

        items = data.get(
            "items",
            []
        )

        if not isinstance(
            items,
            list
        ):
            return jsonify({
                "error":
                    "items muss eine Liste sein"
            }), 400

        # --------------------------------------------------
        # Statistiken
        # --------------------------------------------------

        received = len(items)

        saved = 0

        unchanged = 0

        ignored = 0

        invalid = 0

        # --------------------------------------------------
        # Items verarbeiten
        # --------------------------------------------------

        for api_item in items:

            if not isinstance(
                api_item,
                dict
            ):
                invalid += 1
                continue

            external_id = api_item.get(
                "id"
            )

            price = api_item.get(
                "price"
            )

            # ----------------------------------------------
            # Pflichtfelder prüfen
            # ----------------------------------------------

            if (
                external_id is None
                or price is None
            ):
                invalid += 1
                continue

            try:

                external_id = int(
                    external_id
                )

                price = float(
                    price
                )

            except (
                TypeError,
                ValueError
            ):

                invalid += 1
                continue

            if price < 0:

                invalid += 1
                continue

            # ----------------------------------------------
            # MarketItem suchen
            # ----------------------------------------------

            item = (
                MarketItem.query
                .filter_by(
                    external_id=external_id
                )
                .first()
            )

            # ----------------------------------------------
            # Nicht angelegt
            # ----------------------------------------------

            if not item:

                ignored += 1
                continue

            # ----------------------------------------------
            # Deaktiviert
            # ----------------------------------------------

            if not item.enabled:

                ignored += 1
                continue

            # ----------------------------------------------
            # Letzten Preis holen
            # ----------------------------------------------

            latest = (
                MarketPriceHistory.query
                .filter_by(
                    item_id=item.id
                )
                .order_by(
                    desc(
                        MarketPriceHistory.timestamp
                    )
                )
                .first()
            )

            # ----------------------------------------------
            # Preis unverändert
            # ----------------------------------------------

            if latest:

                try:

                    latest_price = float(
                        latest.price
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    latest_price = None

                if (
                    latest_price is not None
                    and latest_price == price
                ):

                    unchanged += 1
                    continue

            # ----------------------------------------------
            # Neuer Preis
            # ----------------------------------------------

            history = MarketPriceHistory(

                item_id=item.id,

                price=price,

                timestamp=datetime.utcnow(),

            )

            db.session.add(
                history
            )

            saved += 1

        # --------------------------------------------------
        # Einmal committen
        # --------------------------------------------------

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            return jsonify({
                "error":
                    "Fehler beim Speichern der Marktdaten"
            }), 500

        # --------------------------------------------------
        # Ergebnis
        # --------------------------------------------------

        return jsonify({

            "success":
                True,

            "received":
                received,

            "saved":
                saved,

            "unchanged":
                unchanged,

            "ignored":
                ignored,

            "invalid":
                invalid,

        })

    # ======================================================
    # ADMIN
    # ======================================================

    @market.route(
        "/admin"
    )
    def admin():

        if not is_admin():

            return (
                "Keine Berechtigung",
                403
            )

        items = (
            MarketItem.query
            .order_by(
                MarketItem.display_name.asc()
            )
            .all()
        )

        return render_template(
            "market/admin.html",
            items=items,
            acive="market"
        )

    # ======================================================
    # CREATE ITEM
    # ======================================================

    @market.route(
        "/admin/create",
        methods=["POST"]
    )
    def create_item():

        if not is_admin():

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
                    "Keine Daten"
            }), 400

        # --------------------------------------------------
        # External ID
        # --------------------------------------------------

        try:

            external_id = int(
                data.get(
                    "external_id"
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return jsonify({
                "error":
                    "Ungültige externe Item-ID"
            }), 400

        # --------------------------------------------------
        # Name
        # --------------------------------------------------

        name = str(
            data.get(
                "name",
                ""
            )
        ).strip()

        display_name = str(
            data.get(
                "display_name",
                ""
            )
        ).strip()

        if not name:

            return jsonify({
                "error":
                    "Interner Name fehlt"
            }), 400

        if not display_name:

            return jsonify({
                "error":
                    "Anzeigename fehlt"
            }), 400

        # --------------------------------------------------
        # External ID bereits vorhanden?
        # --------------------------------------------------

        if (
            MarketItem.query
            .filter_by(
                external_id=external_id
            )
            .first()
        ):

            return jsonify({
                "error":
                    "Diese externe Item-ID existiert bereits"
            }), 409

        # --------------------------------------------------
        # Interner Name bereits vorhanden?
        # --------------------------------------------------

        if (
            MarketItem.query
            .filter_by(
                name=name
            )
            .first()
        ):

            return jsonify({
                "error":
                    "Dieses Item existiert bereits"
            }), 409

        # --------------------------------------------------
        # Preise
        # --------------------------------------------------

        try:

            min_price = float(
                data.get(
                    "min_price",
                    0
                )
            )

            base_price = float(
                data.get(
                    "base_price",
                    0
                )
            )

            max_price = float(
                data.get(
                    "max_price",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            return jsonify({
                "error":
                    "Ungültige Preise"
            }), 400

        if (
            min_price < 0
            or base_price < 0
            or max_price < 0
        ):

            return jsonify({
                "error":
                    "Preise dürfen nicht negativ sein"
            }), 400

        if not (
            min_price
            <= base_price
            <= max_price
        ):

            return jsonify({
                "error":
                    "Es muss gelten: Min <= Base <= Max"
            }), 400

        # --------------------------------------------------
        # Item erstellen
        # --------------------------------------------------

        item = MarketItem(

            external_id=
                external_id,

            name=
                name,

            display_name=
                display_name,

            min_price=
                min_price,

            base_price=
                base_price,

            max_price=
                max_price,

            enabled=
                bool(
                    data.get(
                        "enabled",
                        True
                    )
                ),

        )

        db.session.add(
            item
        )

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            return jsonify({
                "error":
                    "Fehler beim Erstellen des Items"
            }), 500

        return jsonify({

            "success":
                True,

            "id":
                item.id,

        })

    # ======================================================
    # UPDATE ITEM
    # ======================================================

    @market.route(
        "/admin/<int:item_id>",
        methods=["PUT"]
    )
    def update_item(item_id):

        if not is_admin():

            return jsonify({
                "error":
                    "Keine Berechtigung"
            }), 403

        item = db.session.get(
            MarketItem,
            item_id
        )

        if not item:

            return jsonify({
                "error":
                    "Marktitem nicht gefunden"
            }), 404

        data = request.get_json(
            silent=True
        )

        if not data:

            return jsonify({
                "error":
                    "Keine Daten"
            }), 400

        # --------------------------------------------------
        # External ID
        # --------------------------------------------------

        if "external_id" in data:

            try:

                external_id = int(
                    data["external_id"]
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({
                    "error":
                        "Ungültige externe Item-ID"
                }), 400

            existing = (
                MarketItem.query
                .filter(
                    MarketItem.external_id
                    == external_id,

                    MarketItem.id
                    != item.id,
                )
                .first()
            )

            if existing:

                return jsonify({
                    "error":
                        "Diese externe Item-ID wird bereits verwendet"
                }), 409

            item.external_id = (
                external_id
            )

        # --------------------------------------------------
        # Interner Name
        # --------------------------------------------------

        if "name" in data:

            name = str(
                data["name"]
            ).strip()

            if not name:

                return jsonify({
                    "error":
                        "Name darf nicht leer sein"
                }), 400

            existing = (
                MarketItem.query
                .filter(
                    MarketItem.name
                    == name,

                    MarketItem.id
                    != item.id,
                )
                .first()
            )

            if existing:

                return jsonify({
                    "error":
                        "Dieser interne Name wird bereits verwendet"
                }), 409

            item.name = name

        # --------------------------------------------------
        # Display Name
        # --------------------------------------------------

        if "display_name" in data:

            display_name = str(
                data["display_name"]
            ).strip()

            if not display_name:

                return jsonify({
                    "error":
                        "Anzeigename darf nicht leer sein"
                }), 400

            item.display_name = (
                display_name
            )

        # --------------------------------------------------
        # Preise
        # --------------------------------------------------

        try:

            if "min_price" in data:

                item.min_price = float(
                    data["min_price"]
                )

            if "base_price" in data:

                item.base_price = float(
                    data["base_price"]
                )

            if "max_price" in data:

                item.max_price = float(
                    data["max_price"]
                )

        except (
            TypeError,
            ValueError
        ):

            return jsonify({
                "error":
                    "Ungültiger Preis"
            }), 400

        # --------------------------------------------------
        # Preisvalidierung
        # --------------------------------------------------

        if (
            item.min_price < 0
            or item.base_price < 0
            or item.max_price < 0
        ):

            return jsonify({
                "error":
                    "Preise dürfen nicht negativ sein"
            }), 400

        if not (
            item.min_price
            <= item.base_price
            <= item.max_price
        ):

            return jsonify({
                "error":
                    "Es muss gelten: Min <= Base <= Max"
            }), 400

        # --------------------------------------------------
        # Aktivierung
        # --------------------------------------------------

        if "enabled" in data:

            item.enabled = bool(
                data["enabled"]
            )

        # --------------------------------------------------
        # Speichern
        # --------------------------------------------------

        try:

            db.session.commit()

        except Exception:

            db.session.rollback()

            return jsonify({
                "error":
                    "Fehler beim Speichern"
            }), 500

        return jsonify({
            "success":
                True
        })

    # ======================================================
    # DELETE ITEM
    # ======================================================

    @market.route(
        "/admin/<int:item_id>",
        methods=["DELETE"]
    )
    def delete_item(item_id):

        if not is_admin():

            return jsonify({
                "error":
                    "Keine Berechtigung"
            }), 403

        item = db.session.get(
            MarketItem,
            item_id
        )

        if not item:

            return jsonify({
                "error":
                    "Marktitem nicht gefunden"
            }), 404

        try:

            db.session.delete(
                item
            )

            db.session.commit()

        except Exception:

            db.session.rollback()

            return jsonify({
                "error":
                    "Fehler beim Löschen"
            }), 500

        return jsonify({
            "success":
                True
        })

    # ======================================================
    # RETURN BLUEPRINT
    # ======================================================

    return market