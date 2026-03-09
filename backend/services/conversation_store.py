"""
Conversation storage service for Saarthi.AI.

Uses DynamoDB for atomic, concurrent-safe event storage.

Table: saarthi-sessions  (configurable via SESSIONS_TABLE env var)

Schema
------
  PK  session_id   (string)  — partition key
  SK  event_id     (string)  — sort key: ISO timestamp + "-" + uuid4 suffix
                               guarantees uniqueness even for rapid concurrent writes
  Attributes:
    user_id     string
    query       string
    response    string
    meta        map (optional extra fields)
    expires_at  number  (Unix epoch; used for DynamoDB TTL — 30 days from write)

Enable TTL on 'expires_at' in the DynamoDB table settings to auto-purge old sessions.
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_SESSIONS_TABLE = os.getenv("SESSIONS_TABLE", "saarthi-sessions")
_SESSION_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days

_dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "ap-south-1"))


def _get_table():
    return _dynamodb.Table(_SESSIONS_TABLE)


def append_conversation_event(
    user_id: str,
    session_id: str,
    query: str,
    response: str,
    extra: Dict[str, Any] | None = None,
) -> None:
    """
    Atomically append a single conversation turn to DynamoDB.

    Each call performs ONE PutItem — no read-modify-write, no race conditions.
    All errors are logged as warnings; this function never raises.
    """
    if not user_id:
        user_id = "anonymous"
    if not session_id:
        session_id = "default"

    now_iso = datetime.now(timezone.utc).isoformat()
    # Sort key: timestamp + uuid suffix → unique even for sub-millisecond concurrency
    event_id = f"{now_iso}-{uuid.uuid4().hex[:8]}"

    item: Dict[str, Any] = {
        "session_id": session_id,
        "timestamp": event_id,
        "user_id": user_id,
        "query": query,
        "response": response,
        # FIX: TTL field — DynamoDB will auto-delete after 30 days
        "expires_at": int(time.time()) + _SESSION_TTL_SECONDS,
    }
    if extra:
        item["meta"] = extra

    try:
        table = _get_table()
        table.put_item(Item=item)
        logger.info(
            "Conversation event stored: session=%s event=%s", session_id, event_id
        )
    except ClientError as e:
        logger.warning(
            "DynamoDB ClientError storing conversation event (session=%s): %s",
            session_id,
            str(e),
        )
    except Exception as e:
        logger.warning(
            "Unexpected error storing conversation event (session=%s): %s",
            session_id,
            str(e),
        )
