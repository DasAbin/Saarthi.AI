"""
OpenSearch Serverless client utilities for vector search.
"""

import json
import boto3
import os
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError

# Initialize OpenSearch client
opensearch_client = boto3.client(
    "opensearchserverless",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

# Get OpenSearch endpoint from environment
OPENSEARCH_ENDPOINT = os.getenv("OPENSEARCH_ENDPOINT")
OPENSEARCH_INDEX = os.getenv("OPENSEARCH_INDEX", "saarthi-index")
OPENSEARCH_COLLECTION = os.getenv("OPENSEARCH_COLLECTION", "saarthi-collection")

# Use requests for OpenSearch queries (OpenSearch Serverless uses HTTP)
import requests
from requests.auth import HTTPBasicAuth


def get_opensearch_auth() -> HTTPBasicAuth:
    """
    Get authentication for OpenSearch Serverless.
    Uses IAM credentials from boto3 session.
    """
    session = boto3.Session()
    credentials = session.get_credentials()
    
    # For OpenSearch Serverless, we use AWS Signature V4
    # This is a simplified version - in production, use aws_requests_auth
    return None  # Will use AWS SigV4 signing


def vector_search(
    query_vector: List[float],
    top_k: int = 5,
    filter_dict: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search in OpenSearch Serverless.
    
    Args:
        query_vector: Query embedding vector
        top_k: Number of results to return
        filter_dict: Optional filters
        
    Returns:
        List of search results with metadata
    """
    if not OPENSEARCH_ENDPOINT:
        raise Exception("OPENSEARCH_ENDPOINT not configured")
    
    # OpenSearch Serverless query structure
    query = {
        "size": top_k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_vector,
                    "k": top_k
                }
            }
        },
        "_source": {
            "excludes": ["embedding"]  # Don't return the vector itself
        }
    }
    
    if filter_dict:
        query["query"] = {
            "bool": {
                "must": [
                    {
                        "knn": {
                            "embedding": {
                                "vector": query_vector,
                                "k": top_k
                            }
                        }
                    }
                ],
                "filter": [
                    {"term": {k: v}} for k, v in filter_dict.items()
                ]
            }
        }
    
    url = f"https://{OPENSEARCH_ENDPOINT}/{OPENSEARCH_INDEX}/_search"
    
    try:
        # Use AWS SigV4 signing for requests
        # Option 1: Use aws-requests-auth (install: pip install aws-requests-auth)
        try:
            from aws_requests_auth.aws_auth import AWSRequestsAuth
            
            session = boto3.Session()
            credentials = session.get_credentials()
            region = os.getenv("AWS_REGION", "us-east-1")
            
            auth = AWSRequestsAuth(
                aws_access_key=credentials.access_key,
                aws_secret_access_key=credentials.secret_key,
                aws_token=credentials.token,
                aws_host=OPENSEARCH_ENDPOINT,
                aws_region=region,
                aws_service="aoss"
            )
            
            response = requests.post(
                url,
                json=query,
                auth=auth,
                headers={"Content-Type": "application/json"}
            )
        except ImportError:
            # Option 2: Use boto3's signer (fallback)
            from botocore.auth import SigV4Auth
            from botocore.awsrequest import AWSRequest
            from botocore.credentials import Credentials
            
            session = boto3.Session()
            credentials = session.get_credentials()
            region = os.getenv("AWS_REGION", "us-east-1")
            
            # Create signed request
            request = AWSRequest(method="POST", url=url, data=json.dumps(query))
            SigV4Auth(credentials, "aoss", region).add_auth(request)
            
            response = requests.post(
                url,
                json=query,
                headers=dict(request.headers),
            )
        
        response.raise_for_status()
        results = response.json()
        
        # Format results
        formatted_results = []
        for hit in results.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})
            formatted_results.append({
                "text": source.get("text", ""),
                "source": source.get("source", "Unknown"),
                "page": source.get("page"),
                "score": hit.get("_score", 0.0),
                "metadata": source.get("metadata", {})
            })
        
        return formatted_results
        
    except Exception as e:
        # Fallback: return empty results if OpenSearch is not available
        print(f"OpenSearch error: {str(e)}")
        return []


def index_document(
    doc_id: str,
    text: str,
    embedding: List[float],
    metadata: Dict[str, Any]
) -> bool:
    """
    Index a document in OpenSearch Serverless.
    
    Args:
        doc_id: Unique document ID
        text: Document text
        embedding: Document embedding vector
        metadata: Additional metadata
        
    Returns:
        True if successful
    """
    if not OPENSEARCH_ENDPOINT:
        raise Exception("OPENSEARCH_ENDPOINT not configured")
    
    document = {
        "text": text,
        "embedding": embedding,
        **metadata
    }
    
    url = f"https://{OPENSEARCH_ENDPOINT}/{OPENSEARCH_INDEX}/_doc/{doc_id}"
    
    try:
        from aws_requests_auth.aws_auth import AWSRequestsAuth
        
        session = boto3.Session()
        credentials = session.get_credentials()
        region = os.getenv("AWS_REGION", "us-east-1")
        
        auth = AWSRequestsAuth(
            aws_access_key=credentials.access_key,
            aws_secret_access_key=credentials.secret_key,
            aws_token=credentials.token,
            aws_host=OPENSEARCH_ENDPOINT,
            aws_region=region,
            aws_service="aoss"
        )
        
        response = requests.put(
            url,
            json=document,
            auth=auth,
            headers={"Content-Type": "application/json"}
        )
        
        response.raise_for_status()
        return True
        
    except Exception as e:
        print(f"Failed to index document: {str(e)}")
        return False
