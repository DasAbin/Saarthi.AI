"""
Conversation storage service for Saarthi.AI.

Stores conversations in S3:
  s3://<CONVERSATIONS_BUCKET>/<user_id>/<session_id>.json
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION", "us-east-1"))
_CONV_BUCKET = os.getenv("CONVERSATIONS_BUCKET", "saarthi-conversations")


def append_conversation_event(
    user_id: str,
    session_id: str,
    query: str,
    response: str,
    extra: Dict[str, Any] | None = None,
) -> None:
    """
    Append a conversation turn to the S3 JSON log for this user/session.

    The file is a JSON array of events; we read, append, and write back.
    For hackathon scale this is acceptable; for large scale you'd switch to
    a streaming/event approach.
    """
    if not user_id:
        user_id = "anonymous"
    if not session_id:
        session_id = "default"

    key = f"{user_id}/{session_id}.json"

    try:
        try:
            existing_obj = _s3.get_object(Bucket=_CONV_BUCKET, Key=key)
            existing_body = existing_obj["Body"].read().decode("utf-8")
            events = json.loads(existing_body) if existing_body.strip() else []
            if not isinstance(events, list):
                events = []
        except _s3.exceptions.NoSuchKey:
            events = []
        except Exception as e:
            logger.warning("Could not read existing conversation log: %s", str(e))
            events = []

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query": query,
            "response": response,
        }
        if extra:
            event["meta"] = extra

        events.append(event)

        _s3.put_object(
            Bucket=_CONV_BUCKET,
            Key=key,
            Body=json.dumps(events, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json; charset=utf-8",
        )
    except ClientError as e:
        logger.error("Failed to store conversation in S3: %s", str(e))
    except Exception as e:
        logger.error("Unexpected error storing conversation in S3: %s", str(e))

