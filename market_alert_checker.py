#!/usr/bin/env python3

import sys
import time



# ==========================================================
# STWG MARKET ALERT CHECKER
# ==========================================================

BASE_DIR = "/root/stwg-web"

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ==========================================================
# FLASK APP / DATABASE
# ==========================================================

from main import app
from database import db

from database.models import (
    MarketAlert,
    MarketPriceHistory,
)

from database.models import ActionQueue


# ==========================================================
# SETTINGS
# ==========================================================

CHECK_INTERVAL = 300


# ==========================================================
# CURRENT PRICE
# ==========================================================

def get_current_price(item):

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

    if not latest:
        return None

    return float(latest.price)


# ==========================================================
# TRIGGER
# ==========================================================

def condition_triggered(
    condition,
    current_price,
    target_price
):

    if condition == ">":
        return current_price > target_price

    if condition == "<":
        return current_price < target_price

    return False


# ==========================================================
# REARM
# ==========================================================

def should_rearm(
    condition,
    current_price,
    target_price
):

    if condition == ">":
        return current_price <= target_price

    if condition == "<":
        return current_price >= target_price

    return False


# ==========================================================
# CREATE ACTION
# ==========================================================

def create_discord_action(
    alert,
    current_price
):

    item = alert.item

    if alert.condition == ">":

        text = (
            f"📈 **Preisalarm**\n\n"
            f"🐝 **{item.display_name}**\n\n"
            f"Der Preis ist über deinen Grenzwert gestiegen.\n\n"
            f"💰 Aktueller Preis: "
            f"**{current_price:,.2f}**\n"
            f"🎯 Grenzwert: "
            f"**{float(alert.target_price):,.2f}**"
        )

    else:

        text = (
            f"📉 **Preisalarm**\n\n"
            f"🐝 **{item.display_name}**\n\n"
            f"Der Preis ist unter deinen Grenzwert gefallen.\n\n"
            f"💰 Aktueller Preis: "
            f"**{current_price:,.2f}**\n"
            f"🎯 Grenzwert: "
            f"**{float(alert.target_price):,.2f}**"
        )

    action = ActionQueue(
        key="send_user_message",
        data={
            "userId": str(alert.user_id),
            "text": text,
        }
    )

    return action


# ==========================================================
# CHECK ALERTS
# ==========================================================

def check_alerts():

    alerts = (
        MarketAlert.query
        .filter_by(
            enabled=True
        )
        .all()
    )

    if not alerts:

        print(
            "[INFO] Keine aktiven Preisalarme."
        )

        return

    triggered = 0
    rearmed = 0

    for alert in alerts:

        try:

            current_price = get_current_price(
                alert.item
            )

            if current_price is None:

                print(
                    f"[SKIP] "
                    f"{alert.item.display_name}: "
                    f"kein Preis vorhanden."
                )

                continue

            target_price = float(
                alert.target_price
            )

            # ==================================================
            # ALARM SCHARF
            # ==================================================

            if alert.armed:

                if condition_triggered(
                    alert.condition,
                    current_price,
                    target_price
                ):

                    print(
                        f"[TRIGGER] "
                        f"{alert.item.display_name} "
                        f"{current_price} "
                        f"{alert.condition} "
                        f"{target_price}"
                    )

                    action = create_discord_action(
                        alert,
                        current_price
                    )

                    # ActionQueue hinzufügen
                    db.session.add(action)

                    # Alarm deaktivieren
                    alert.armed = False

                    triggered += 1

            # ==================================================
            # ALARM WIEDER SCHARF
            # ==================================================

            else:

                if should_rearm(
                    alert.condition,
                    current_price,
                    target_price
                ):

                    alert.armed = True

                    rearmed += 1

                    print(
                        f"[REARM] "
                        f"{alert.item.display_name}: "
                        f"{current_price}"
                    )

            # aktuellen Preis speichern
            alert.last_price = current_price

        except Exception as e:

            print(
                f"[ERROR] "
                f"Alarm {alert.id}: {e}"
            )

    db.session.commit()

    print(
        f"[CHECK] "
        f"{len(alerts)} Alarme | "
        f"{triggered} ausgelöst | "
        f"{rearmed} rearmed"
    )


# ==========================================================
# MAIN
# ==========================================================

def main():

    print("=" * 60)
    print("STWG MARKET ALERT CHECKER")
    print("=" * 60)

    print(
        f"[INFO] Prüfintervall: "
        f"{CHECK_INTERVAL} Sekunden"
    )

    while True:

        try:

            with app.app_context():

                check_alerts()

        except KeyboardInterrupt:

            print(
                "[INFO] Checker beendet."
            )

            break

        except Exception as e:

            print(
                f"[ERROR] "
                f"{e}"
            )

        time.sleep(
            CHECK_INTERVAL
        )


if __name__ == "__main__":
    main()