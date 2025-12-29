import logging
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), "../logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "assistant.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("UserSupportAssistant")
