from flask import Blueprint, render_template


def legal_blueprint() -> Blueprint:
    legal = Blueprint(
        "legal",
        __name__,
        url_prefix="/legal"
    )

    @legal.get("/impressum")
    def impressum():
        return render_template("legal/impressum.html")

    @legal.get("/datenschutz")
    def datenschutz():
        return render_template("legal/datenschutz.html")

    return legal