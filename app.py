from main import create_app
from lib.logger import configure_logging
import logging
logger = logging.getLogger("LAUNCHER")

if __name__ == '__main__':
    configure_logging()
    logger.info("setting up app")
    app = create_app()
    logger.info("running: app")
    app.run(debug=True, host="0.0.0.0", port=9999)
