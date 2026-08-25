from blueprints.status import status_blueprint
from blueprints.auth import auth_blueprint
from blueprints.rules import rules_blueprint
from blueprints.user import user_blueprint
from blueprints.tickets import tickets_bp
from blueprints.settings import settings_bp

from blueprints.meeting import meeting_blueprint
from blueprints.warehouse import warehouse_blueprint
from blueprints.voice_credits import voice_credits_blueprint
from blueprints.wasp import wasp_blueprint
from blueprints.document import document_blueprint
from blueprints.messaging import messaging_bp

from blueprints.market import market_blueprint

from blueprints.market_alerts import market_alert_blueprint
from blueprints.training import training_bp

from blueprints.license_management import license_management
from blueprints.jetpack import jetpack_blueprint
# Services
from blueprints.control.grabber_control import grabber_control_bp
from blueprints.control.market_alert_checker_control import market_alert_checker_control_bp
from blueprints.control.bot_control import bot_control_bp

def register_blueprints(app):
    app.register_blueprint(
    jetpack_blueprint()
    )

    app.register_blueprint(training_bp)
    app.register_blueprint(
    grabber_control_bp
    )
    app.register_blueprint(
    license_management  
    )
    app.register_blueprint(
    market_alert_checker_control_bp
    )
    app.register_blueprint(
    market_alert_blueprint()
    )
    app.register_blueprint(bot_control_bp)
    app.register_blueprint(market_blueprint())
    
    app.register_blueprint(status_blueprint(), url_prefix="/status")

    app.register_blueprint(user_blueprint())

    app.register_blueprint(auth_blueprint())

    app.register_blueprint(tickets_bp)
    app.register_blueprint(settings_bp)

    app.register_blueprint(
        messaging_bp,
        url_prefix="/messaging"
    )

    app.register_blueprint(rules_blueprint())
    app.register_blueprint(meeting_blueprint())
    app.register_blueprint(warehouse_blueprint())
    app.register_blueprint(voice_credits_blueprint())
    app.register_blueprint(wasp_blueprint())
    app.register_blueprint(document_blueprint())