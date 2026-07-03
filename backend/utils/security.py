"""
=============================================================================
backend/utils/security.py — WEBHOOK SECURITY
=============================================================================
GitHub aur Slack requests ko verify karo — fake requests reject karo.
HMAC-SHA256 signature verification.
=============================================================================
"""

import hashlib
import hmac
import time

from backend.core.config import settings
from backend.core.logger import get_logger

logger = get_logger(__name__)


# def verify_github_signature(payload_bytes: bytes, signature_header: str | None) -> bool:
#     """
#     GitHub webhook signature verify karo.
#     Header: X-Hub-Signature-256: sha256=<hmac>
#     """
#     if not signature_header or not signature_header.startswith("sha256="):
#         logger.warning("[Security] GitHub: missing or invalid signature header")
#         return False

#     expected = hmac.new(
#         settings.github_webhook_secret.encode(),
#         payload_bytes,
#         hashlib.sha256,
#     ).hexdigest()

#     valid = hmac.compare_digest(f"sha256={expected}", signature_header)
#     if not valid:
#         logger.warning("[Security] GitHub: signature mismatch")
#     return valid

# def verify_github_signature(payload_bytes: bytes, signature_header: str | None) -> bool:
#     """
#     GitHub webhook signature verify karo.
#     """
#     if not signature_header or not signature_header.startswith("sha256="):
#         logger.warning("[Security] GitHub: missing or invalid signature header")
#         return False

#     # Secret ko bytes mein convert karo
#     secret = settings.github_webhook_secret.encode("utf-8")
    
#     # HMAC calculation
#     hmac_obj = hmac.new(secret, payload_bytes, hashlib.sha256)
#     expected_signature = hmac_obj.hexdigest()

#     # Compare with header
#     valid = hmac.compare_digest(f"sha256={expected_signature}", signature_header)

#     if not valid:
#         logger.warning("[Security] GitHub: signature mismatch")
#         logger.debug(f"Expected : {expected}")
#         logger.debug(f"Received : {signature_header}")
#         logger.debug(f"Secret length: {len(settings.github_webhook_secret)}")
#         logger.debug(f"Payload length: {len(payload_bytes)} bytes")
#     else:
#         logger.info("[Security] GitHub: signature verified successfully ✅")
    
#     return valid

def verify_github_signature(payload_bytes: bytes, signature_header: str | None) -> bool:
    """
    GitHub webhook signature verify karo.
    """
    if not signature_header or not signature_header.startswith("sha256="):
        logger.warning("[Security] GitHub: missing or invalid signature header")
        return False

    secret = settings.github_webhook_secret.encode("utf-8")
    
    hmac_obj = hmac.new(secret, payload_bytes, hashlib.sha256)
    expected_signature = hmac_obj.hexdigest()
    expected = f"sha256={expected_signature}"

    valid = hmac.compare_digest(expected, signature_header)

    if not valid:
        logger.warning("[Security] GitHub: signature mismatch")
        logger.error(f"Expected  : {expected}")           # ← error level pe
        logger.error(f"Received  : {signature_header}")   # ← error level pe
        logger.error(f"Secret Length : {len(settings.github_webhook_secret)}")
        logger.error(f"Payload Length: {len(payload_bytes)} bytes")
    else:
        logger.info("[Security] GitHub: signature verified successfully ✅")

    return valid

def verify_slack_signature(
    body:      bytes,
    timestamp: str | None,
    signature: str | None,
) -> bool:
    """
    Slack webhook signature verify karo.
    Headers: X-Slack-Request-Timestamp + X-Slack-Signature
    5 minute se purani requests reject karo (replay attack prevention).
    """
    if not timestamp or not signature:
        logger.warning("[Security] Slack: missing signature headers")
        return False

    try:
        if abs(time.time() - float(timestamp)) > 300:
            logger.warning("[Security] Slack: request too old (replay attack?)")
            return False
    except ValueError:
        return False

    base      = f"v0:{timestamp}:{body.decode()}"
    computed  = hmac.new(
        settings.slack_signing_secret.encode(),
        base.encode(),
        hashlib.sha256,
    ).hexdigest()

    valid = hmac.compare_digest(f"v0={computed}", signature)
    if not valid:
        logger.warning("[Security] Slack: signature mismatch")
    return valid
