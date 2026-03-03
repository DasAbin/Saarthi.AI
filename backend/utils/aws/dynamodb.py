"""
DynamoDB client utilities for vector storage and metadata.

Stores document chunks with:
- Text content
- Embeddings (as binary or JSON)
- Metadata (source, page, etc.)
"""

import json
import boto3
import os
import logging
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError
import base64

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-1"))
dynamodb_client = boto3.client("dynamodb", region_name=os.getenv("AWS_REGION", "us-east-1"))

# Table name from environment
TABLE_NAME = os.getenv("DYNAMODB_TABLE", "saarthi-vectors")


def get_table():
    """Get DynamoDB table instance."""
    return dynamodb.Table(TABLE_NAME)


def store_chunk(
    chunk_id: str,
    text: str,
    embedding: List[float],
    metadata: Dict[str, Any]
) -> bool:
    """
    Store a document chunk with embedding in DynamoDB.
    
    Args:
        chunk_id: Unique chunk identifier
        text: Chunk text content
        embedding: Embedding vector (list of floats)
        metadata: Additional metadata (source, page, etc.)
        
    Returns:
        True if successful
    """
    try:
        table = get_table()
        
        # Convert embedding to JSON string for storage
        # DynamoDB can store lists, but JSON string is more reliable
        embedding_json = json.dumps(embedding)
        
        item = {
            "chunk_id": chunk_id,
            "text": text,
            "embedding": embedding_json,  # Store as JSON string
            "embedding_dim": len(embedding),
            **metadata  # Add metadata fields
        }
        
        table.put_item(Item=item)
        logger.debug(f"Stored chunk: {chunk_id}")
        return True
        
    except ClientError as e:
        logger.error(f"Failed to store chunk {chunk_id}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error storing chunk: {str(e)}")
        return False


def get_chunk(chunk_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a chunk by ID.
    
    Args:
        chunk_id: Chunk identifier
        
    Returns:
        Chunk data or None if not found
    """
    try:
        table = get_table()
        response = table.get_item(Key={"chunk_id": chunk_id})
        
        if "Item" not in response:
            return None
        
        item = response["Item"]
        
        # Parse embedding from JSON string
        if "embedding" in item:
            item["embedding"] = json.loads(item["embedding"])
        
        return item
        
    except Exception as e:
        logger.error(f"Error retrieving chunk {chunk_id}: {str(e)}")
        return None


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    import math
    
    if len(vec1) != len(vec2):
        raise ValueError("Vectors must have same dimension")
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(a * a for a in vec2))
    
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


def vector_search(
    query_embedding: List[float],
    top_k: int = 5,
    filter_dict: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Search for similar vectors in DynamoDB using cosine similarity.
    
    Note: This performs a full table scan, which is not efficient for large tables.
    For production, consider using FAISS for vector search and DynamoDB for metadata.
    
    Args:
        query_embedding: Query embedding vector
        top_k: Number of results to return
        filter_dict: Optional filters (e.g., {"source": "document.pdf"})
        
    Returns:
        List of similar chunks with scores, sorted by similarity
    """
    try:
        table = get_table()
        
        # Scan table (inefficient but works for small-medium datasets)
        # For production, use FAISS + DynamoDB hybrid approach
        scan_kwargs = {}
        
        if filter_dict:
            # Build filter expression using boto3 conditions
            from boto3.dynamodb.conditions import Attr
            
            filter_conditions = None
            for key, value in filter_dict.items():
                condition = Attr(key).eq(value)
                if filter_conditions is None:
                    filter_conditions = condition
                else:
                    filter_conditions = filter_conditions & condition
            
            if filter_conditions:
                scan_kwargs["FilterExpression"] = filter_conditions
        
        results = []
        
        # Scan with pagination
        while True:
            response = table.scan(**scan_kwargs)
            
            for item in response.get("Items", []):
                try:
                    # Parse embedding
                    if "embedding" in item:
                        chunk_embedding = json.loads(item["embedding"])
                    else:
                        continue
                    
                    # Calculate similarity
                    similarity = cosine_similarity(query_embedding, chunk_embedding)
                    
                    # Build result
                    result = {
                        "chunk_id": item.get("chunk_id"),
                        "text": item.get("text", ""),
                        "source": item.get("source", "Unknown"),
                        "page": item.get("page"),
                        "score": similarity,
                        "metadata": {k: v for k, v in item.items() if k not in ["embedding", "embedding_dim"]}
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.warning(f"Error processing chunk: {str(e)}")
                    continue
            
            # Check for more pages
            if "LastEvaluatedKey" not in response:
                break
            
            scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        
        # Sort by score (descending) and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
        
    except Exception as e:
        logger.error(f"Error in vector search: {str(e)}")
        return []


def create_table_if_not_exists():
    """
    Create DynamoDB table if it doesn't exist.
    
    Table structure:
    - Partition key: chunk_id (String)
    - Attributes: text, embedding, source, page, etc.
    """
    try:
        table = get_table()
        table.load()  # Check if table exists
        logger.info(f"Table {TABLE_NAME} already exists")
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            # Table doesn't exist, create it
            try:
                table = dynamodb.create_table(
                    TableName=TABLE_NAME,
                    KeySchema=[
                        {"AttributeName": "chunk_id", "KeyType": "HASH"}
                    ],
                    AttributeDefinitions=[
                        {"AttributeName": "chunk_id", "AttributeType": "S"}
                    ],
                    BillingMode="PAY_PER_REQUEST"  # On-demand pricing
                )
                logger.info(f"Created table {TABLE_NAME}")
                table.wait_until_exists()
                return True
            except Exception as create_error:
                logger.error(f"Failed to create table: {str(create_error)}")
                return False
        else:
            logger.error(f"Error checking table: {str(e)}")
            return False
