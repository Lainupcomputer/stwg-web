import os
import time
import requests

from datetime import datetime, timezone

from flask import Flask
from dotenv import load_dotenv

from database import db
from database.models import (
    MarketItem,
    MarketPriceHistory,
    DataStorage
)


# ==========================================================
# ENV
# ==========================================================

load_dotenv()


# ==========================================================
# FLASK APP
# ==========================================================

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+mysqlconnector://"
    f"{os.getenv('DB_USER')}:"
    f"{os.getenv('DB_PASSWORD')}@"
    f"{os.getenv('DB_HOST')}:"
    f"{os.getenv('DB_PORT')}/"
    f"{os.getenv('DB_NAME')}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# ==========================================================
# API
# ==========================================================

API_URL = "https://ucp-api.lyl.gg/market.php"

HEADERS = {
    "Accept": "application/json",
    "Origin": "https://ucp.lyl.gg",
    "Referer": "https://ucp.lyl.gg/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}


# ==========================================================
# DATENBANK / DATA STORAGE
# ==========================================================

def get_storage_value(key, default=None):
    """
    Liest einen Wert aus DataStorage.
    """

    try:

        entry = (
            DataStorage.query
            .filter_by(key=key)
            .first()
        )

        if entry is None:
            return default

        return entry.data

    except Exception as e:

        print(
            f"[ERROR] DataStorage '{key}' "
            f"konnte nicht gelesen werden: {e}"
        )

        return default


def get_grabber_config():
    """
    Liest die aktuelle Grabber-Konfiguration
    aus DataStorage.

    Keys:

        market_grabber_api_key
        market_grabber_interval
    """

    api_key = get_storage_value(
        "ucp.auth_key"
    )

    interval_raw = get_storage_value(
        "ucp.poll_intervall",
        "300"
    )

    try:

        interval = int(interval_raw)

    except (
        TypeError,
        ValueError
    ):

        print(
            "[WARNING] Ungültiges Grabber-Intervall "
            f"'{interval_raw}'. Verwende 300 Sekunden."
        )

        interval = 300

    # Sicherheitsgrenze
    if interval < 10:

        print(
            "[WARNING] Grabber-Intervall ist kleiner "
            "als 10 Sekunden. Verwende 10 Sekunden."
        )

        interval = 10

    return api_key, interval


# ==========================================================
# GRABBER
# ==========================================================

def grab_market():
    """
    Führt genau einen Markt-Grabber-Durchlauf aus.
    """

    print()
    print("=" * 60)
    print("STWG MARKET GRABBER")
    print("=" * 60)


    # ======================================================
    # KONFIGURATION AUS DB
    # ======================================================

    with app.app_context():

        api_key, interval = get_grabber_config()


    if not api_key:

        print(
            "[ERROR] Kein API-Key in DataStorage gefunden."
        )

        print(
            "[ERROR] Erwarteter Key: "
            "market_grabber_api_key"
        )

        return False


    print(
        f"[INFO] Grabber-Intervall: "
        f"{interval} Sekunden"
    )


    # ======================================================
    # API REQUEST
    # ======================================================

    headers = {
        **HEADERS,
        "Authorization": api_key,
    }


    try:

        response = requests.get(
            API_URL,
            headers=headers,
            timeout=15,
        )

        response.raise_for_status()

        raw = response.json()

    except requests.RequestException as e:

        print(
            f"[ERROR] API Fehler: {e}"
        )

        return False

    except ValueError as e:

        print(
            f"[ERROR] JSON Fehler: {e}"
        )

        return False


    # ======================================================
    # API DATA
    # ======================================================

    api_items = raw.get(
        "data",
        []
    )


    if not isinstance(
        api_items,
        list
    ):

        print(
            "[ERROR] API Antwort enthält kein gültiges "
            "'data'-Array."
        )

        return False


    print(
        f"[INFO] API liefert "
        f"{len(api_items)} Items."
    )


    # ======================================================
    # DATENBANK
    # ======================================================

    with app.app_context():

        items = (
            MarketItem.query
            .filter_by(enabled=True)
            .all()
        )


        print(
            f"[INFO] {len(items)} Marktitems überwacht."
        )


        if not items:

            print(
                "[INFO] Keine aktivierten Marktitems."
            )

            return True


        # ==================================================
        # API ITEMS INDEXIEREN
        # ==================================================

        api_by_id = {}


        for api_item in api_items:

            try:

                api_id = int(
                    api_item["id"]
                )

                api_by_id[api_id] = api_item

            except (
                KeyError,
                TypeError,
                ValueError
            ):

                continue


        # ==================================================
        # STATISTIK
        # ==================================================

        saved = 0
        skipped = 0
        unchanged = 0
        errors = 0


        # ==================================================
        # ITEMS VERARBEITEN
        # ==================================================

        for item in items:

            external_id = item.external_id


            # ------------------------------------------------
            # KEINE API-ID
            # ------------------------------------------------

            if external_id is None:

                print(
                    f"[SKIP] {item.display_name}: "
                    f"keine API-ID."
                )

                skipped += 1

                continue


            # ------------------------------------------------
            # API-ID KONVERTIEREN
            # ------------------------------------------------

            try:

                external_id = int(
                    external_id
                )

            except (
                TypeError,
                ValueError
            ):

                print(
                    f"[ERROR] {item.display_name}: "
                    f"ungültige API-ID."
                )

                errors += 1

                continue


            # ------------------------------------------------
            # API ITEM SUCHEN
            # ------------------------------------------------

            api_item = api_by_id.get(
                external_id
            )


            if not api_item:

                print(
                    f"[SKIP] {item.display_name}: "
                    f"API-ID {external_id} "
                    f"nicht gefunden."
                )

                skipped += 1

                continue


            # ------------------------------------------------
            # PREIS
            # ------------------------------------------------

            try:

                price = float(
                    api_item["price"]
                )

            except (
                KeyError,
                TypeError,
                ValueError
            ):

                print(
                    f"[ERROR] {item.display_name}: "
                    f"ungültiger Preis."
                )

                errors += 1

                continue


            # ------------------------------------------------
            # LETZTEN PREIS HOLEN
            # ------------------------------------------------

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


            # ------------------------------------------------
            # PREIS UNVERÄNDERT?
            # ------------------------------------------------

            if latest:

                try:

                    old_price = float(
                        latest.price
                    )


                    if old_price == price:

                        print(
                            f"[UNCHANGED] "
                            f"{item.display_name:<30} "
                            f"{price:>10.2f}"
                        )

                        unchanged += 1

                        continue

                except (
                    TypeError,
                    ValueError
                ):

                    pass


            # ------------------------------------------------
            # HISTORIE SPEICHERN
            # ------------------------------------------------

            history = MarketPriceHistory(
                item_id=item.id,
                price=price,
                timestamp=datetime.now(
                    timezone.utc
                ),
            )


            db.session.add(
                history
            )


            saved += 1


            print(
                f"[SAVED] "
                f"{item.display_name:<30} "
                f"{price:>10.2f}"
            )


        # ==================================================
        # COMMIT
        # ==================================================

        try:

            db.session.commit()

        except Exception as e:

            db.session.rollback()

            print(
                f"[ERROR] Datenbankfehler: {e}"
            )

            return False


    # ======================================================
    # AUSGABE
    # ======================================================

    print()
    print("=" * 60)
    print("GRABBER ABGESCHLOSSEN")
    print("=" * 60)

    print(
        f"API Items      : {len(api_items)}"
    )

    print(
        f"Überwacht      : {len(items)}"
    )

    print(
        f"Gespeichert    : {saved}"
    )

    print(
        f"Unverändert    : {unchanged}"
    )

    print(
        f"Übersprungen   : {skipped}"
    )

    print(
        f"Fehler         : {errors}"
    )

    print("=" * 60)

    return True


# ==========================================================
# DAUERBETRIEB
# ==========================================================

def main():

    print()
    print("=" * 60)
    print("STWG MARKET GRABBER")
    print("DAUERBETRIEB GESTARTET")
    print("=" * 60)


    while True:

        # ==================================================
        # EINEN DURCHLAUF AUSFÜHREN
        # ==================================================

        try:

            grab_market()

        except KeyboardInterrupt:

            print()
            print(
                "[INFO] Grabber wird beendet."
            )

            break

        except Exception as e:

            print()
            print(
                f"[ERROR] Unerwarteter Fehler: {e}"
            )


        # ==================================================
        # INTERVALL ERNEUT AUS DB LESEN
        # ==================================================

        with app.app_context():

            _, interval = get_grabber_config()


        print()
        print(
            f"[INFO] Nächster Grabber-Lauf "
            f"in {interval} Sekunden."
        )


        # ==================================================
        # WARTEN
        # ==================================================

        try:

            time.sleep(
                interval
            )

        except KeyboardInterrupt:

            print()
            print(
                "[INFO] Grabber wird beendet."
            )

            break


# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":

    main()