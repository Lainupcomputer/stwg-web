from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for,
    flash
)
from database import db
from database.models import Warehouse, WarehouseItem, UserProfile


WAREHOUSE_CAPACITY = 20000


def warehouse_blueprint():
    warehouse = Blueprint(
        "warehouse",
        __name__,
        url_prefix="/warehouse"
    )

    def get_current_user():

        discord_user = session.get("user")

        if not discord_user:

            return None

        discord_id = discord_user.get("id")

        if not discord_id:
            return None

        try:
            discord_id = int(discord_id)
        except (TypeError, ValueError):
            return None

        return (
            UserProfile.query
            .filter(
                UserProfile.user_id == discord_id,
                UserProfile.is_member.is_(True)
            )
            .first()
        )


    def is_admin():

        return bool(
            session.get("is_admin")
        )


    def get_warehouse_weight():

        entries = (
            Warehouse.query
            .all()
        )

        total_weight = 0.0

        for entry in entries:

            if not entry.item_data:
                continue

            item_weight = float(
                entry.item_data.weight or 0
            )

            amount = int(
                entry.amount or 0
            )

            total_weight += (
                item_weight * amount
            )

        return total_weight


    def get_free_warehouse_weight():

        return max(
            0.0,
            WAREHOUSE_CAPACITY -
            get_warehouse_weight()
        )


        # ------------------------------------------------------
        # LOGIN
        # ------------------------------------------------------

        user = get_current_user()

        if not user:
            return redirect(
                url_for("auth.login")
            )

        # ------------------------------------------------------
        # ALLE WAREHOUSE EINTRÄGE
        # ------------------------------------------------------

        warehouse_entries = (
            Warehouse.query
            .order_by(
                Warehouse.user_name.asc()
            )
            .all()
        )

        # ------------------------------------------------------
        # ITEMS
        # ------------------------------------------------------

        items = (
            WarehouseItem.query
            .order_by(
                WarehouseItem.name.asc()
            )
            .all()
        )


    @warehouse.route("/view", methods=["GET"])
    def view():

        if not is_admin():

            return redirect(
                url_for("auth.login")
            )

        warehouses = (
            Warehouse.query
            .order_by(
                Warehouse.user_name.asc()
            )
            .all()
        )

        users = (
            UserProfile.query
            .filter(
                UserProfile.is_member.is_(True)
            )
            .order_by(
                UserProfile.username.asc()
            )
            .all()
        )

        items = (
            WarehouseItem.query
            .order_by(
                WarehouseItem.name.asc()
            )
            .all()
        )

        total_weight = (
            get_warehouse_weight()
        )

        free_weight = (
            get_free_warehouse_weight()
        )

        return render_template(
            "warehouse/view.html",
            active="warehouse",
            warehouses=warehouses,
            users=users,
            items=items,
            warehouse_capacity=WAREHOUSE_CAPACITY,
            total_weight=total_weight,
            free_weight=free_weight
        )


    @warehouse.route("/update", methods=["POST"])
    def update():

        if not is_admin():

            return jsonify({
                "success": False,
                "message":
                    "Keine Berechtigung."
            }), 403

        try:

            data = request.get_json()

            if not data:

                return jsonify({
                    "success": False,
                    "message":
                        "Keine Daten erhalten."
                }), 400

            warehouse_id = data.get(
                "id"
            )

            action = data.get(
                "action"
            )

            amount = data.get(
                "amount"
            )

            if action not in (
                "increase",
                "decrease",
                "set"
            ):

                return jsonify({
                    "success": False,
                    "message":
                        "Ungültige Aktion."
                }), 400

            try:

                amount = int(
                    amount
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({
                    "success": False,
                    "message":
                        "Ungültige Menge."
                }), 400

            if amount < 0:

                return jsonify({
                    "success": False,
                    "message":
                        "Die Menge darf nicht negativ sein."
                }), 400

            entry = (
                Warehouse.query
                .filter(
                    Warehouse.id == warehouse_id
                )
                .first()
            )

            if not entry:

                return jsonify({
                    "success": False,
                    "message":
                        "Eintrag nicht gefunden."
                }), 404

            if not entry.item_data:

                return jsonify({
                    "success": False,
                    "message":
                        "Für diesen Gegenstand ist kein Gewicht hinterlegt."
                }), 400

            item_weight = float(
                entry.item_data.weight or 0
            )

            old_amount = int(
                entry.amount or 0
            )

            old_weight = (
                old_amount *
                item_weight
            )

            if action == "increase":

                new_amount = (
                    old_amount +
                    amount
                )

            elif action == "decrease":

                new_amount = max(
                    0,
                    old_amount - amount
                )

            else:

                new_amount = amount

            new_weight = (
                new_amount *
                item_weight
            )

            weight_difference = (
                new_weight -
                old_weight
            )

            current_weight = (
                get_warehouse_weight()
            )

            if (
                weight_difference > 0
                and
                current_weight +
                weight_difference >
                WAREHOUSE_CAPACITY
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "Nicht genügend Platz im Warenhaus.",

                    "free_weight":
                        get_free_warehouse_weight()

                }), 400

            entry.amount = new_amount

            if new_amount == 0:

                db.session.delete(
                    entry
                )

            db.session.commit()

            return jsonify({

                "success": True,

                "amount": new_amount,

                "total_weight":
                    get_warehouse_weight(),

                "free_weight":
                    get_free_warehouse_weight(),

                "message":
                    "Menge wurde geändert."

            })

        except Exception as e:

            db.session.rollback()

            print(
                "Warehouse Admin Update Fehler:",
                e
            )

            return jsonify({

                "success": False,

                "message":
                    "Fehler beim Ändern der Menge."

            }), 500


    @warehouse.route("/create", methods=["POST"])
    def create():

        if not is_admin():

            return jsonify({
                "success": False,
                "message":
                    "Keine Berechtigung."
            }), 403

        try:

            data = request.get_json()

            if not data:

                return jsonify({
                    "success": False,
                    "message":
                        "Keine Daten erhalten."
                }), 400

            user_id = data.get(
                "user_id"
            )

            item_id = data.get(
                "item_id"
            )

            amount = data.get(
                "amount"
            )

            # --------------------------------------------------
            # USER
            # --------------------------------------------------

            try:
                user_id = int(
                    user_id
                )
            except (
                TypeError,
                ValueError
            ):
                return jsonify({
                    "success": False,
                    "message":
                        "Ungültiger Benutzer."
                }), 400

            user = (
                UserProfile.query
                .filter(
                    UserProfile.user_id == user_id,
                    UserProfile.is_member.is_(True)
                )
                .first()
            )

            if not user:

                return jsonify({
                    "success": False,
                    "message":
                        "Ungültiger Besitzer."
                }), 400

            # --------------------------------------------------
            # ITEM
            # --------------------------------------------------

            try:
                item_id = int(
                    item_id
                )
            except (
                TypeError,
                ValueError
            ):
                return jsonify({
                    "success": False,
                    "message":
                        "Ungültiger Gegenstand."
                }), 400

            item = (
                WarehouseItem.query
                .filter(
                    WarehouseItem.id == item_id
                )
                .first()
            )

            if not item:

                return jsonify({
                    "success": False,
                    "message":
                        "Ungültiger Gegenstand."
                }), 400

            # --------------------------------------------------
            # MENGE
            # --------------------------------------------------

            try:

                amount = int(
                    amount
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({
                    "success": False,
                    "message":
                        "Ungültige Menge."
                }), 400

            if amount <= 0:

                return jsonify({
                    "success": False,
                    "message":
                        "Die Menge muss größer als 0 sein."
                }), 400

            # --------------------------------------------------
            # GEWICHT
            # --------------------------------------------------

            additional_weight = (
                amount *
                float(item.weight or 0)
            )

            if (
                get_warehouse_weight() +
                additional_weight >
                WAREHOUSE_CAPACITY
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "Nicht genügend Platz im Warenhaus.",

                    "free_weight":
                        get_free_warehouse_weight()

                }), 400

            # --------------------------------------------------
            # EXISTIERENDEN EINTRAG
            # --------------------------------------------------

            entry = (
                Warehouse.query
                .filter(
                    Warehouse.user_id ==
                    user.user_id,

                    Warehouse.item_id ==
                    item.id
                )
                .first()
            )

            if entry:

                entry.amount += amount

            else:

                entry = Warehouse(

                    user_id=
                        user.user_id,

                    user_name=
                        user.username,

                    item_id=
                        item.id,

                    amount=
                        amount
                )

                db.session.add(
                    entry
                )

            db.session.commit()

            return jsonify({

                "success": True,

                "message":
                    "Warehouse-Eintrag wurde erstellt.",

                "total_weight":
                    get_warehouse_weight(),

                "free_weight":
                    get_free_warehouse_weight()

            }), 201

        except Exception as e:

            db.session.rollback()

            print(
                "Warehouse Admin Create Fehler:",
                e
            )

            return jsonify({

                "success": False,

                "message":
                    "Fehler beim Erstellen des Eintrags."

            }), 500


    @warehouse.route("/edit", methods=["POST"])
    def edit():

        if not is_admin():

            return jsonify({
                "success": False,
                "message":
                    "Keine Berechtigung."
            }), 403

        try:

            data = request.get_json()

            if not data:

                return jsonify({
                    "success": False,
                    "message":
                        "Keine Daten erhalten."
                }), 400

            warehouse_id = data.get(
                "id"
            )

            user_id = data.get(
                "user_id"
            )

            item_id = data.get(
                "item_id"
            )

            # --------------------------------------------------
            # EINTRAG
            # --------------------------------------------------

            entry = (
                Warehouse.query
                .filter(
                    Warehouse.id == warehouse_id
                )
                .first()
            )

            if not entry:

                return jsonify({
                    "success": False,
                    "message":
                        "Eintrag nicht gefunden."
                }), 404

            # --------------------------------------------------
            # USER
            # --------------------------------------------------

            try:
                user_id = int(
                    user_id
                )
            except (
                TypeError,
                ValueError
            ):
                return jsonify({
                    "success": False,
                    "message":
                        "Ungültiger Benutzer."
                }), 400

            user = (
                UserProfile.query
                .filter(
                    UserProfile.user_id == user_id,
                    UserProfile.is_member.is_(True)
                )
                .first()
            )

            if not user:

                return jsonify({
                    "success": False,
                    "message":
                        "Ungültiger Besitzer."
                }), 400

            # --------------------------------------------------
            # ITEM
            # --------------------------------------------------

            try:
                item_id = int(
                    item_id
                )
            except (
                TypeError,
                ValueError
            ):
                return jsonify({
                    "success": False,
                    "message":
                        "Ungültiger Gegenstand."
                }), 400

            item = (
                WarehouseItem.query
                .filter(
                    WarehouseItem.id == item_id
                )
                .first()
            )

            if not item:

                return jsonify({
                    "success": False,
                    "message":
                        "Ungültiger Gegenstand."
                }), 400

            # --------------------------------------------------
            # ALTES / NEUES GEWICHT
            # --------------------------------------------------

            old_item_weight = float(
                entry.item_data.weight or 0
            )

            new_item_weight = float(
                item.weight or 0
            )

            old_weight = (
                entry.amount *
                old_item_weight
            )

            new_weight = (
                entry.amount *
                new_item_weight
            )

            weight_difference = (
                new_weight -
                old_weight
            )

            current_weight = (
                get_warehouse_weight()
            )

            # --------------------------------------------------
            # KAPAZITÄT
            # --------------------------------------------------

            if (
                weight_difference > 0
                and
                current_weight +
                weight_difference >
                WAREHOUSE_CAPACITY
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "Die Änderung würde die "
                        "maximale Lagerkapazität überschreiten.",

                    "free_weight":
                        get_free_warehouse_weight()

                }), 400

            # --------------------------------------------------
            # ÄNDERN
            # --------------------------------------------------

            entry.user_id = (
                user.user_id
            )

            entry.user_name = (
                user.username
            )

            entry.item_id = (
                item.id
            )

            db.session.commit()

            return jsonify({

                "success": True,

                "message":
                    "Eintrag wurde geändert.",

                "total_weight":
                    get_warehouse_weight(),

                "free_weight":
                    get_free_warehouse_weight()

            })

        except Exception as e:

            db.session.rollback()

            print(
                "Warehouse Admin Edit Fehler:",
                e
            )

            return jsonify({

                "success": False,

                "message":
                    "Fehler beim Bearbeiten."

            }), 500


    @warehouse.route("/delete", methods=["POST"])
    def delete():

        if not is_admin():

            return jsonify({
                "success": False,
                "message":
                    "Keine Berechtigung."
            }), 403

        try:

            data = request.get_json()

            if not data:

                return jsonify({
                    "success": False,
                    "message":
                        "Keine Daten erhalten."
                }), 400

            warehouse_id = data.get(
                "id"
            )

            entry = (
                Warehouse.query
                .filter(
                    Warehouse.id == warehouse_id
                )
                .first()
            )

            if not entry:

                return jsonify({
                    "success": False,
                    "message":
                        "Eintrag nicht gefunden."
                }), 404

            db.session.delete(
                entry
            )

            db.session.commit()

            return jsonify({

                "success": True,

                "message":
                    "Eintrag wurde gelöscht.",

                "total_weight":
                    get_warehouse_weight(),

                "free_weight":
                    get_free_warehouse_weight()

            })

        except Exception as e:

            db.session.rollback()

            print(
                "Warehouse Admin Delete Fehler:",
                e
            )

            return jsonify({

                "success": False,

                "message":
                    "Fehler beim Löschen."

            }), 500

   
    @warehouse.route("/items", methods=["GET"])
    def items():

        if not is_admin():

            return redirect(
                url_for("auth.login")
            )

        items = (
            WarehouseItem.query
            .order_by(
                WarehouseItem.name.asc()
            )
            .all()
        )

        return render_template(
            "warehouse/items.html",
            active="warehouse",
            items=items
        )


    @warehouse.route("/items/create", methods=["POST"])
    def create_item():

        if not is_admin():

            return jsonify({
                "success": False,
                "message":
                    "Keine Berechtigung."
            }), 403

        try:

            data = request.get_json()

            if not data:

                return jsonify({
                    "success": False,
                    "message":
                        "Keine Daten erhalten."
                }), 400

            name = data.get(
                "name",
                ""
            ).strip()

            weight = data.get(
                "weight"
            )

            if not name:

                return jsonify({
                    "success": False,
                    "message":
                        "Bitte einen Namen angeben."
                }), 400

            try:

                weight = float(
                    weight
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({
                    "success": False,
                    "message":
                        "Ungültiges Gewicht."
                }), 400

            if weight < 0:

                return jsonify({
                    "success": False,
                    "message":
                        "Das Gewicht darf nicht negativ sein."
                }), 400

            existing = (
                WarehouseItem.query
                .filter(
                    WarehouseItem.name == name
                )
                .first()
            )

            if existing:

                return jsonify({
                    "success": False,
                    "message":
                        "Dieser Gegenstand existiert bereits."
                }), 400

            item = WarehouseItem(

                name=name,

                weight=weight
            )

            db.session.add(
                item
            )

            db.session.commit()

            return jsonify({

                "success": True,

                "message":
                    "Gegenstand wurde erstellt.",

                "id":
                    item.id

            }), 201

        except Exception as e:

            db.session.rollback()

            print(
                "Warehouse Item Create Fehler:",
                e
            )

            return jsonify({

                "success": False,

                "message":
                    "Fehler beim Erstellen."

            }), 500


    @warehouse.route("/items/edit", methods=["POST"])
    def edit_item():

        if not is_admin():

            return jsonify({
                "success": False,
                "message":
                    "Keine Berechtigung."
            }), 403

        try:

            data = request.get_json()

            if not data:

                return jsonify({
                    "success": False,
                    "message":
                        "Keine Daten erhalten."
                }), 400

            item_id = data.get(
                "id"
            )

            name = data.get(
                "name",
                ""
            ).strip()

            weight = data.get(
                "weight"
            )

            item = (
                WarehouseItem.query
                .filter(
                    WarehouseItem.id == item_id
                )
                .first()
            )

            if not item:

                return jsonify({
                    "success": False,
                    "message":
                        "Gegenstand nicht gefunden."
                }), 404

            if not name:

                return jsonify({
                    "success": False,
                    "message":
                        "Bitte einen Namen angeben."
                }), 400

            try:

                weight = float(
                    weight
                )

            except (
                TypeError,
                ValueError
            ):

                return jsonify({
                    "success": False,
                    "message":
                        "Ungültiges Gewicht."
                }), 400

            if weight < 0:

                return jsonify({
                    "success": False,
                    "message":
                        "Das Gewicht darf nicht negativ sein."
                }), 400

            # --------------------------------------------------
            # DOPPELTEN NAMEN PRÜFEN
            # --------------------------------------------------

            duplicate = (
                WarehouseItem.query
                .filter(
                    WarehouseItem.name == name,
                    WarehouseItem.id != item.id
                )
                .first()
            )

            if duplicate:

                return jsonify({
                    "success": False,
                    "message":
                        "Dieser Name wird bereits verwendet."
                }), 400

            # --------------------------------------------------
            # GEWICHT DES GESAMTEN ITEMS
            # --------------------------------------------------

            old_weight_total = 0.0

            entries = (
                Warehouse.query
                .filter(
                    Warehouse.item_id == item.id
                )
                .all()
            )

            for entry in entries:

                old_weight_total += (
                    entry.amount *
                    float(item.weight or 0)
                )

            new_weight_total = 0.0

            for entry in entries:

                new_weight_total += (
                    entry.amount *
                    weight
                )

            weight_difference = (
                new_weight_total -
                old_weight_total
            )

            current_weight = (
                get_warehouse_weight()
            )

            # --------------------------------------------------
            # KAPAZITÄT
            # --------------------------------------------------

            if (
                weight_difference > 0
                and
                current_weight +
                weight_difference >
                WAREHOUSE_CAPACITY
            ):

                return jsonify({

                    "success": False,

                    "message":
                        "Das neue Gewicht würde "
                        "die Lagerkapazität überschreiten.",

                    "free_weight":
                        get_free_warehouse_weight()

                }), 400

            # --------------------------------------------------
            # ÄNDERN
            # --------------------------------------------------

            item.name = name
            item.weight = weight

            db.session.commit()

            return jsonify({

                "success": True,

                "message":
                    "Gegenstand wurde geändert.",

                "total_weight":
                    get_warehouse_weight(),

                "free_weight":
                    get_free_warehouse_weight()

            })

        except Exception as e:

            db.session.rollback()

            print(
                "Warehouse Item Edit Fehler:",
                e
            )

            return jsonify({

                "success": False,

                "message":
                    "Fehler beim Bearbeiten."

            }), 500


    @warehouse.route("/items/delete", methods=["POST"])
    def delete_item():

        if not is_admin():

            return jsonify({
                "success": False,
                "message":
                    "Keine Berechtigung."
            }), 403

        try:

            data = request.get_json()

            if not data:

                return jsonify({
                    "success": False,
                    "message":
                        "Keine Daten erhalten."
                }), 400

            item_id = data.get(
                "id"
            )

            item = (
                WarehouseItem.query
                .filter(
                    WarehouseItem.id == item_id
                )
                .first()
            )

            if not item:

                return jsonify({
                    "success": False,
                    "message":
                        "Gegenstand nicht gefunden."
                }), 404

            # --------------------------------------------------
            # NOCH IM WAREHOUSE VERWENDET?
            # --------------------------------------------------

            usage = (
                Warehouse.query
                .filter(
                    Warehouse.item_id == item.id
                )
                .first()
            )

            if usage:

                return jsonify({

                    "success": False,

                    "message":
                        "Der Gegenstand wird noch "
                        "im Warenhaus verwendet und "
                        "kann deshalb nicht gelöscht werden."

                }), 400

            db.session.delete(
                item
            )

            db.session.commit()

            return jsonify({

                "success": True,

                "message":
                    "Gegenstand wurde gelöscht."

            })

        except Exception as e:

            db.session.rollback()

            print(
                "Warehouse Item Delete Fehler:",
                e
            )

            return jsonify({

                "success": False,

                "message":
                    "Fehler beim Löschen."

            }), 500

        # ==========================================================
   

    @warehouse.route("/my", methods=["GET"])
    def my():
        user = get_current_user()


        if not user:

            return redirect(
                url_for("auth.login")
            )

        # Alle Einträge anzeigen
        warehouses = (
            Warehouse.query
            .order_by(
                Warehouse.user_name.asc()
            )
            .all()
        )

        # Alle verfügbaren Items
        items = (
            WarehouseItem.query
            .order_by(
                WarehouseItem.name.asc()
            )
            .all()
        )

        # Alle Mitglieder für Übertragungen
        users = (
            UserProfile.query
            .filter(
                UserProfile.is_member.is_(True),
                UserProfile.user_id != user.user_id
            )
            .order_by(
                UserProfile.username.asc()
            )
            .all()
        )

        return render_template(
            "warehouse/my.html",
            active="my_warehouse",
            warehouses=warehouses,
            items=items,
            users=users,
            current_user=user,
            warehouse_capacity=WAREHOUSE_CAPACITY,
            total_weight=get_warehouse_weight(),
            free_weight=get_free_warehouse_weight()
        )


    @warehouse.route("/my/create", methods=["POST"])
    def my_create():

        user = get_current_user()

        if not user:
            return jsonify({
                "success": False,
                "message": "Nicht eingeloggt."
            }), 401

        try:

            data = request.get_json()

            if not data:
                return jsonify({
                    "success": False,
                    "message": "Keine Daten erhalten."
                }), 400

            item_id = data.get("item_id")
            amount = data.get("amount")

            # --------------------------------------------------
            # ITEM
            # --------------------------------------------------

            try:
                item_id = int(item_id)
            except (TypeError, ValueError):

                return jsonify({
                    "success": False,
                    "message": "Ungültiger Gegenstand."
                }), 400

            item = (
                WarehouseItem.query
                .filter(
                    WarehouseItem.id == item_id
                )
                .first()
            )

            if not item:

                return jsonify({
                    "success": False,
                    "message": "Gegenstand nicht gefunden."
                }), 404

            # --------------------------------------------------
            # MENGE
            # --------------------------------------------------

            try:
                amount = int(amount)
            except (TypeError, ValueError):

                return jsonify({
                    "success": False,
                    "message": "Ungültige Menge."
                }), 400

            if amount <= 0:

                return jsonify({
                    "success": False,
                    "message":
                        "Die Menge muss größer als 0 sein."
                }), 400

            # --------------------------------------------------
            # EXISTIERENDEN EINTRAG PRÜFEN
            # --------------------------------------------------

            entry = (
                Warehouse.query
                .filter(
                    Warehouse.user_id == user.user_id,
                    Warehouse.item_id == item.id
                )
                .first()
            )

            # Wenn bereits vorhanden, wird die Menge erhöht
            additional_weight = (
                amount *
                float(item.weight or 0)
            )

            if (
                get_warehouse_weight() +
                additional_weight >
                WAREHOUSE_CAPACITY
            ):

                return jsonify({
                    "success": False,
                    "message":
                        "Nicht genügend Platz im Warenhaus.",
                    "free_weight":
                        get_free_warehouse_weight()
                }), 400

            # --------------------------------------------------
            # EINTRAG ERSTELLEN / ERHÖHEN
            # --------------------------------------------------

            if entry:

                entry.amount += amount

            else:

                entry = Warehouse(
                    user_id=user.user_id,
                    user_name=user.username,
                    item_id=item.id,
                    amount=amount
                )

                db.session.add(entry)

            db.session.commit()

            return jsonify({
                "success": True,
                "message":
                    "Warehouse-Eintrag wurde erstellt.",
                "total_weight":
                    get_warehouse_weight(),
                "free_weight":
                    get_free_warehouse_weight()
            }), 201

        except Exception as e:

            db.session.rollback()

            print(
                "Warehouse User Create Fehler:",
                e
            )

            return jsonify({
                "success": False,
                "message":
                    "Fehler beim Erstellen des Eintrags."
            }), 500


    @warehouse.route("/my/update", methods=["POST"])
    def my_update():

        user = get_current_user()

        if not user:
            return jsonify({
                "success": False,
                "message": "Nicht eingeloggt."
            }), 401

        try:

            data = request.get_json()

            if not data:
                return jsonify({
                    "success": False,
                    "message": "Keine Daten erhalten."
                }), 400

            warehouse_id = data.get("id")
            action = data.get("action")
            amount = data.get("amount")

            if action not in (
                "increase",
                "decrease",
                "set"
            ):

                return jsonify({
                    "success": False,
                    "message": "Ungültige Aktion."
                }), 400

            try:
                warehouse_id = int(warehouse_id)
                amount = int(amount)
            except (TypeError, ValueError):

                return jsonify({
                    "success": False,
                    "message": "Ungültige Daten."
                }), 400

            if amount < 0:

                return jsonify({
                    "success": False,
                    "message":
                        "Die Menge darf nicht negativ sein."
                }), 400

            # --------------------------------------------------
            # WICHTIG:
            # NUR EIGENER EINTRAG
            # --------------------------------------------------

            entry = (
                Warehouse.query
                .filter(
                    Warehouse.id == warehouse_id,
                    Warehouse.user_id == user.user_id
                )
                .first()
            )

            if not entry:

                return jsonify({
                    "success": False,
                    "message":
                        "Eintrag nicht gefunden oder keine Berechtigung."
                }), 404

            if not entry.item_data:

                return jsonify({
                    "success": False,
                    "message":
                        "Für diesen Gegenstand ist kein Gewicht hinterlegt."
                }), 400

            item_weight = float(
                entry.item_data.weight or 0
            )

            old_amount = int(
                entry.amount or 0
            )

            old_weight = (
                old_amount *
                item_weight
            )

            # --------------------------------------------------
            # NEUE MENGE
            # --------------------------------------------------

            if action == "increase":

                new_amount = (
                    old_amount +
                    amount
                )

            elif action == "decrease":

                new_amount = max(
                    0,
                    old_amount - amount
                )

            else:

                new_amount = amount

            new_weight = (
                new_amount *
                item_weight
            )

            weight_difference = (
                new_weight -
                old_weight
            )

            current_weight = (
                get_warehouse_weight()
            )

            # --------------------------------------------------
            # KAPAZITÄT
            # --------------------------------------------------

            if (
                weight_difference > 0
                and
                current_weight +
                weight_difference >
                WAREHOUSE_CAPACITY
            ):

                return jsonify({
                    "success": False,
                    "message":
                        "Nicht genügend Platz im Warenhaus.",
                    "free_weight":
                        get_free_warehouse_weight()
                }), 400

            # --------------------------------------------------
            # ÄNDERN / LÖSCHEN
            # --------------------------------------------------

            entry.amount = new_amount

            if new_amount == 0:

                db.session.delete(entry)

            db.session.commit()

            return jsonify({
                "success": True,
                "amount": new_amount,
                "total_weight":
                    get_warehouse_weight(),
                "free_weight":
                    get_free_warehouse_weight(),
                "message":
                    "Menge wurde geändert."
            })

        except Exception as e:

            db.session.rollback()

            print(
                "Warehouse User Update Fehler:",
                e
            )

            return jsonify({
                "success": False,
                "message":
                    "Fehler beim Ändern der Menge."
            }), 500


    @warehouse.route("/my/delete", methods=["POST"])
    def my_delete():

        user = get_current_user()

        if not user:
            return jsonify({
                "success": False,
                "message": "Nicht eingeloggt."
            }), 401

        try:

            data = request.get_json()

            if not data:
                return jsonify({
                    "success": False,
                    "message": "Keine Daten erhalten."
                }), 400

            warehouse_id = data.get("id")

            try:
                warehouse_id = int(warehouse_id)
            except (TypeError, ValueError):

                return jsonify({
                    "success": False,
                    "message":
                        "Ungültiger Eintrag."
                }), 400

            # --------------------------------------------------
            # NUR EIGENER EINTRAG
            # --------------------------------------------------

            entry = (
                Warehouse.query
                .filter(
                    Warehouse.id == warehouse_id,
                    Warehouse.user_id == user.user_id
                )
                .first()
            )

            if not entry:

                return jsonify({
                    "success": False,
                    "message":
                        "Eintrag nicht gefunden oder keine Berechtigung."
                }), 404

            db.session.delete(entry)

            db.session.commit()

            return jsonify({
                "success": True,
                "message":
                    "Eintrag wurde gelöscht.",
                "total_weight":
                    get_warehouse_weight(),
                "free_weight":
                    get_free_warehouse_weight()
            })

        except Exception as e:

            db.session.rollback()

            print(
                "Warehouse User Delete Fehler:",
                e
            )

            return jsonify({
                "success": False,
                "message":
                    "Fehler beim Löschen."
            }), 500


    @warehouse.route("/my/transfer", methods=["POST"])
    def my_transfer():

        user = get_current_user()

        if not user:
            return jsonify({
                "success": False,
                "message": "Nicht eingeloggt."
            }), 401

        try:

            data = request.get_json()

            if not data:
                return jsonify({
                    "success": False,
                    "message": "Keine Daten erhalten."
                }), 400

            warehouse_id = data.get("id")
            target_user_id = data.get("user_id")
            amount = data.get("amount")

            # --------------------------------------------------
            # DATEN
            # --------------------------------------------------

            try:
                warehouse_id = int(warehouse_id)
                target_user_id = int(target_user_id)
                amount = int(amount)
            except (TypeError, ValueError):

                return jsonify({
                    "success": False,
                    "message":
                        "Ungültige Daten."
                }), 400

            if amount <= 0:

                return jsonify({
                    "success": False,
                    "message":
                        "Die Menge muss größer als 0 sein."
                }), 400

            # --------------------------------------------------
            # QUELL-EINTRAG
            # --------------------------------------------------

            source = (
                Warehouse.query
                .filter(
                    Warehouse.id == warehouse_id,
                    Warehouse.user_id == user.user_id
                )
                .first()
            )

            if not source:

                return jsonify({
                    "success": False,
                    "message":
                        "Eintrag nicht gefunden oder keine Berechtigung."
                }), 404

            # --------------------------------------------------
            # GENUG MENGE?
            # --------------------------------------------------

            source_amount = int(
                source.amount or 0
            )

            if amount > source_amount:

                return jsonify({
                    "success": False,
                    "message":
                        "Du besitzt nicht genügend Stück."
                }), 400

            # --------------------------------------------------
            # ZIELUSER
            # --------------------------------------------------

            target_user = (
                UserProfile.query
                .filter(
                    UserProfile.user_id == target_user_id,
                    UserProfile.is_member.is_(True)
                )
                .first()
            )

            if not target_user:

                return jsonify({
                    "success": False,
                    "message":
                        "Der Zielbenutzer ist kein gültiges Mitglied."
                }), 400

            if target_user.user_id == user.user_id:

                return jsonify({
                    "success": False,
                    "message":
                        "Du kannst nicht an dich selbst übertragen."
                }), 400

            # --------------------------------------------------
            # ZIEL-EINTRAG
            # --------------------------------------------------

            target = (
                Warehouse.query
                .filter(
                    Warehouse.user_id ==
                        target_user.user_id,
                    Warehouse.item_id ==
                        source.item_id
                )
                .first()
            )

            # --------------------------------------------------
            # ÜBERTRAGEN
            # --------------------------------------------------

            if target:

                target.amount += amount

            else:

                target = Warehouse(
                    user_id=target_user.user_id,
                    user_name=target_user.username,
                    item_id=source.item_id,
                    amount=amount
                )

                db.session.add(target)

            # Quelle reduzieren
            source.amount -= amount

            if source.amount <= 0:

                db.session.delete(source)

            db.session.commit()

            return jsonify({
                "success": True,
                "message":
                    "Menge wurde erfolgreich übertragen.",
                "total_weight":
                    get_warehouse_weight(),
                "free_weight":
                    get_free_warehouse_weight()
            })

        except Exception as e:

            db.session.rollback()

            print(
                "Warehouse User Transfer Fehler:",
                e
            )

            return jsonify({
                "success": False,
                "message":
                    "Fehler beim Übertragen."
            }), 500

    return warehouse
