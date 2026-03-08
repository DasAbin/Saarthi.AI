"""
DynamoDB-backed query cache for RAG answers.

Table: QueryCache (name configurable via QUERY_CACHE_TABLE env var)

Partition key: query_hash (string)
Attributes: response (JSON string), timestamp (ISO string), expires_at (number, TTL)

Note: Enable DynamoDB TTL on the 'expires_at' attribute in the AWS Console
(or via CDK/CloudFormation) for automatic item expiry.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "ap-south-1"))
_CACHE_TABLE_NAME = os.getenv("QUERY_CACHE_TABLE", "saarthi-query-cache")

# Cache TTL in seconds (default: 24 hours). Set CACHE_TTL_SECONDS env var to override.
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "86400"))


def _get_table():
    return _dynamodb.Table(_CACHE_TABLE_NAME)


def make_query_hash(query: str, language: str, document_id: Optional[str]) -> str:
    """
    Create a stable hash for (query, language, document_id).

    Normalises query with strip + lower so "PMAY" and "pmay" map to the
    same cache entry.
    """
    key = json.dumps(
        # FIX: .strip().lower() ensures case-insensitive cache hits
        {"q": query.strip().lower(), "lang": language, "doc": document_id or ""},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def get_cached_response(
    query_hash: str,
) -> Optional[Dict[str, Any]]:
    """
    Fetch a cached response by hash, if present and not expired.

    Note: DynamoDB TTL deletion is eventual (up to 48 h lag), so we also
    check expires_at manually to avoid serving stale items.
    """
    try:
        table = _get_table()
        resp = table.get_item(Key={"query_hash": query_hash})
        item = resp.get("Item")
        if not item:
            return None

        # Manual TTL check in case DynamoDB hasn't reaped the item yet
        expires_at = item.get("expires_at")
        if expires_at and int(time.time()) > int(expires_at):
            logger.info("Cache item expired (expires_at=%s), treating as miss", expires_at)
            return None

        raw = item.get("response")
        if not raw:
            return None

        return json.loads(raw)
    except ClientError as e:
        logger.error("Error reading query cache: %s", str(e))
        return None
    except Exception as e:
        logger.error("Unexpected error reading query cache: %s", str(e))
        return None


def put_cached_response(query_hash: str, response_body: Dict[str, Any]) -> None:
    """
    Store a response in the cache with a TTL expiry timestamp.

    To enable automatic DynamoDB-level deletion you must set the TTL attribute
    name to 'expires_at' in your DynamoDB table settings (Console → Table →
    Additional settings → Time to Live).
    """
    try:
        table = _get_table()
        table.put_item(
            Item={
                "query_hash": query_hash,
                "response": json.dumps(response_body, ensure_ascii=False),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                # FIX: unix epoch TTL for DynamoDB native expiry
                "expires_at": int(time.time()) + CACHE_TTL_SECONDS,
            }
        )
    except ClientError as e:
        logger.error("Error writing query cache: %s", str(e))
    except Exception as e:
        logger.error("Unexpected error writing query cache: %s", str(e))
