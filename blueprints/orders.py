from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database import db
from database.models import OrderItem, ActionQueue
from helper.perms import require_role_management

orders_bp = Blueprint("orders", __name__, template_folder="templates", url_prefix="/orders")


# --- Hauptseite: Bestellungen anzeigen ---
@orders_bp.route("/", methods=["GET"])
def orders_home():
    items = OrderItem.query.all()
    categories = ["weapons", "vehicle", "equipment", "components"]
    categorized_items = {cat: [] for cat in categories}
    for item in items:
        if item.category in categories:
            categorized_items[item.category].append(item)
    return render_template("orders/home.html", categorized_items=categorized_items, active="orders")


# --- Preisliste bearbeiten ---
@orders_bp.route("/price_list", methods=["GET"])
@require_role_management
def price_list():
    items = OrderItem.query.all()
    categories = ["vehicle", "equipment", "components"]
    categorized_items = {cat: [] for cat in categories}
    for item in items:
        if item.category in categories:
            categorized_items[item.category].append(item)
    return render_template("orders/price_list.html", categorized_items=categorized_items, active="prices")



@orders_bp.route("/pricelist_pub", methods=["GET"])
def public_pricelist():
    items = OrderItem.query.all()
    categories = ["vehicle", "equipment", "components"]
    categorized_items = {cat: [] for cat in categories}
    for item in items:
        if item.category in categories:
            categorized_items[item.category].append(item)
    return render_template("pub_pricelist.html", categorized_items=categorized_items)


# --- API: Item erstellen ---
@orders_bp.route("/item", methods=["POST"])
@require_role_management
def add_item():

    data = request.get_json()
    if not data:
        return jsonify({"error": "Keine Daten"}), 400
    category = data.get("category")
    name = data.get("name")
    price = data.get("price")
    if not category or not name or not price:
        return jsonify({"error": "Fehlende Felder"}), 400

    # Max 20 pro Kategorie prüfen
    count = OrderItem.query.filter_by(category=category).count()
    if count >= 20:
         return jsonify({"error": "Max. 20 Items pro Kategorie erreicht"}), 400

    item = OrderItem(category=category, name=name, price=price)
    db.session.add(item)
    db.session.commit()
    return jsonify({"message": "Item hinzugefügt", "id": item.id})


# --- API: Item löschen ---
@orders_bp.route("/item/<int:item_id>", methods=["DELETE"])
@require_role_management
def delete_item(item_id):
    item = OrderItem.query.get(item_id)
    if not item:
        return jsonify({"error": "Item nicht gefunden"}), 404
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item gelöscht"})


# --- API: Item bearbeiten ---
@orders_bp.route("/item/<int:item_id>", methods=["PUT"])
@require_role_management
def update_item(item_id):
    item = OrderItem.query.get(item_id)
    if not item:
        return jsonify({"error": "Item nicht gefunden"}), 404
    data = request.get_json()
    item.name = data.get("name", item.name)
    item.price = data.get("price", item.price)
    db.session.commit()
    return jsonify({"message": "Item aktualisiert"})


@orders_bp.route("/update_message")
@require_role_management
def update_message():
    action = ActionQueue(
        key="update_order_message",
        data={"action": "action"}
    )
    db.session.add(action)
    db.session.commit()
    return redirect(url_for("orders.pricelist"))

@orders_bp.route("/stats")
@require_role_management
def stats_view():
    return render_template("orders/stats.html")