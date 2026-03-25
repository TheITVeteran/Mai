import logging

import requests

logger = logging.getLogger(__name__)

API_URL = "http://localhost:1234/api/v1/chat"
REQUEST_TIMEOUT_S = 120

payload = {
    "model": "l3-8b-stheno-v3.2-iq-imatrix",
    "input": "Say hello!",
}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s [%(name)s] %(message)s")
    try:
        response = requests.post(
            API_URL, json=payload, timeout=REQUEST_TIMEOUT_S
        )
        logger.info("Status Code: %s", response.status_code)
        logger.info("Response: %s", response.json())
    except Exception:
        logger.exception("LM Studio request failed")
