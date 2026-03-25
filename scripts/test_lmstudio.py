import logging

from mai.lmstudio import extract_assistant_text, post_chat

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
        data = post_chat(API_URL, payload, timeout=float(REQUEST_TIMEOUT_S))
        logger.info("Assistant text: %s", extract_assistant_text(data))
    except Exception:
        logger.exception("LM Studio request failed")
