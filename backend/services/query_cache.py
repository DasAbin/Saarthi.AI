"""
DynamoDB-backed query cache for RAG answers.

Table: QueryCache (name configurable via QUERY_CACHE_TABLE env var)

Partition key: query_hash (string)
Attributes: response (JSON string), timestamp (ISO string)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-1"))
_CACHE_TABLE_NAME = os.getenv("QUERY_CACHE_TABLE", "saarthi-query-cache")


def _get_table():
    return _dynamodb.Table(_CACHE_TABLE_NAME)


def make_query_hash(query: str, language: str, document_id: Optional[str]) -> str:
    """
    Create a stable hash for (query, language, document_id).
    """
    key = json.dumps(
        {"q": query.strip(), "lang": language, "doc": document_id or ""},
        sort_keys=True,
        ensure_ascii=False,
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def get_cached_response(
    query_hash: str,
) -> Optional[Dict[str, Any]]:
    """
    Fetch a cached response by hash, if present.
    """
    try:
        table = _get_table()
        resp = table.get_item(Key={"query_hash": query_hash})
        item = resp.get("Item")
        if not item:
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
    Store a response in the cache.
    """
    try:
        table = _get_table()
        table.put_item(
            Item={
                "query_hash": query_hash,
                "response": json.dumps(response_body, ensure_ascii=False),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
    except ClientError as e:
        logger.error("Error writing query cache: %s", str(e))
    except Exception as e:
        logger.error("Unexpected error writing query cache: %s", str(e))

