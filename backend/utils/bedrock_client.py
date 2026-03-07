"""
AWS Bedrock client utilities for LLM and embeddings.
"""

import json
import boto3
import os
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

# Model IDs
CLAUDE_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
TITAN_EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"


def get_embedding(text: str) -> List[float]:
    """
    Get embedding for a single text using Amazon Titan Embeddings.
    
    Args:
        text: Input text to embed
        
    Returns:
        List of floats representing the embedding vector
    """
    try:
        body = json.dumps({"inputText": text})
        
        response = bedrock_runtime.invoke_model(
            modelId=TITAN_EMBEDDING_MODEL_ID,
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response["body"].read())
        return response_body["embedding"]
    except ClientError as e:
        raise Exception(f"Failed to get embedding: {str(e)}")


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings for multiple texts.
    
    Args:
        texts: List of input texts
        
    Returns:
        List of embedding vectors
    """
    embeddings = []
    for text in texts:
        embeddings.append(get_embedding(text))
    return embeddings


def invoke_claude(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7
) -> str:
    """
    Invoke Claude 3 Sonnet via Bedrock.
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        
    Returns:
        Generated text response
    """
    try:
        messages = [{"role": "user", "content": prompt}]
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }
        
        if system_prompt:
            body["system"] = system_prompt
        
        response = bedrock_runtime.invoke_model(
            modelId=CLAUDE_MODEL_ID,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        
        response_body = json.loads(response["body"].read())
        
        # Extract text from response
        if "content" in response_body and len(response_body["content"]) > 0:
            return response_body["content"][0]["text"]
        else:
            raise Exception("Empty response from Claude")
            
    except ClientError as e:
        raise Exception(f"Failed to invoke Claude: {str(e)}")


def format_rag_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Format RAG prompt with retrieved context.
    
    Args:
        query: User query
        context_chunks: List of retrieved context chunks with metadata
        
    Returns:
        Formatted prompt string
    """
    context_text = "\n\n".join([
        f"[Source: {chunk.get('source', 'Unknown')}, Page: {chunk.get('page', 'N/A')}]\n{chunk.get('text', '')}"
        for chunk in context_chunks
    ])
    
    prompt = f"""You are a helpful AI assistant that provides accurate information about Indian government schemes and policies.

Use the following context to answer the user's question. If the context doesn't contain enough information, say so clearly.

Context:
{context_text}

User Question: {query}

Provide a clear, accurate answer based on the context above. Include citations to sources when relevant."""
    
    return prompt
