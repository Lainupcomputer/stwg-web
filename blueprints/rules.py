from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash
from database import db
from database.models import RuleField, DataStorage
from dhooks import Webhook, Embed
from requests import HTTPError


def rules_blueprint():
    rules = Blueprint("rules", __name__, url_prefix="/rules")

    @rules.route("/view", methods=["GET"])
    def view_rules():
        if session.get("is_admin"):
            return render_template("rules/rules.html", active="rules")
        else:
            return redirect(url_for("auth.login"))

    @rules.route("/view_public", methods=["GET"])
    def view_rules_public():
        return render_template("rules/public.html", active="rules")

    @rules.route("/add_rule", methods=["GET"])
    def add_rule():
        if session.get("is_admin"):
            return render_template("rules/create.html", active="rules")
        else:
            return redirect(url_for("auth.login"))

    @rules.route("/", methods=["GET"])
    def get_rules():
        all_rules = RuleField.query.all()
        return jsonify([
            {"id": r.id, "title": r.title, "content": r.content, "inline": r.inline}
            for r in all_rules
        ])


    @rules.route("/", methods=["POST"])
    def create_rule():
        if session.get("is_admin"):
            data = request.get_json()
            if not data or "title" not in data or "content" not in data:
                return jsonify({"error": "Missing title or content"}), 400

            new_rule = RuleField(
                title=data["title"],
                content=data["content"],
                inline=data.get("inline", False)
            )
            db.session.add(new_rule)
            db.session.commit()
            return jsonify({"id": new_rule.id, "title": new_rule.title,
                            "content": new_rule.content, "inline": new_rule.inline}), 201
        else:
            return redirect(url_for("auth.login"))

    @rules.route("/<int:rule_id>", methods=["PUT"])
    def update_rule(rule_id):
        if session.get("is_admin"):
            data = request.get_json()
            if not data or "title" not in data or "content" not in data:
                return jsonify({"error": "Missing title or content"}), 400

            rule = RuleField.query.get(rule_id)
            if not rule:
                return jsonify({"error": "Rule not found"}), 404

            rule.title = data["title"]
            rule.content = data["content"]
            rule.inline = data.get("inline", False)

            db.session.commit()
            return jsonify({"id": rule.id, "title": rule.title,
                            "content": rule.content, "inline": rule.inline})
        else:
            return redirect(url_for("auth.login"))

    @rules.route("/<int:rule_id>", methods=["DELETE"])
    def delete_rule(rule_id):
        if session.get("is_admin"):
            rule = RuleField.query.get(rule_id)
            if not rule:
                return jsonify({"error": "Rule not found"}), 404

            db.session.delete(rule)
            db.session.commit()
            return jsonify({"message": "Deleted successfully"})
        else:
            return redirect(url_for("auth.login"))

    @rules.route("/send")
    def send_rules_via_hook():
        if session.get("is_admin"):
            rule_hook_url = DataStorage.query.filter_by(key="hooks.rule_hook_url").first()
            user_announcement_hook_url = DataStorage.query.filter_by(key="hooks.announcement_hook_url").first()
            rule_hook = Webhook(rule_hook_url.data)
            announcement_hook = Webhook(user_announcement_hook_url.data)

            announcement_embed = Embed(
                title="📢 Aktualisierung des Regelwerks",
                description=(
                    "Wir möchten euch informieren, dass sich unsere **Server-Regeln geändert haben**.\n\n"
                    "Bitte lest euch die neuen Regeln durch. "
                    "Die Änderungen gelten **ab sofort**."
                ),
                color=0x992D22
            )
            announcement_embed.set_footer(text="Danke für eure Aufmerksamkeit!")
            rule_embed = Embed(
                title="📜 Fraktions-Regelwerk",
                description="Bitte halte dich jederzeit an die folgenden Regeln und vertrete die Fraktion mit Loyalität, Respekt und Engagement.",
                color=0x992D22
            )

            fields = RuleField.query.all()
            if not fields:
                rule_embed.add_field(
                    name="Keine Regeln",
                    value="Das Regelwerk ist derzeit leer.",
                    inline=False
                )
            else:
                for field in fields:
                    rule_embed.add_field(
                        name=field.title,
                        value=field.content,
                        inline=field.inline
                    )

            rule_embed.set_footer(text="⚖️ Fraktionsleitung behält sich Änderungen jederzeit vor.")

            try:
                rule_hook.send(embed=rule_embed)
            except HTTPError:
                flash("Konnte Regeln nicht senden, Webhook Url ist Falsch.")
            except ValueError:
                flash("Konnte Regeln nicht senden, Webhook Url ist nicht  vorhanden.")

            try:
                announcement_hook.send(embed=announcement_embed)
            except HTTPError:
                flash("Konnte Announcement nicht senden, Webhook Url ist Falsch.")
            except ValueError:
                flash("Konnte Announcement nicht senden, Webhook Url ist nicht  vorhanden.")

            return redirect(url_for("rules.view_rules"))
        else:
            return redirect(url_for("auth.login"))

    return rules
