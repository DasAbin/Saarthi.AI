"""
AWS Bedrock client utilities for LLM and embeddings.

Uses:
- Amazon Nova (Lite/Micro/Pro) for text generation via Bedrock Converse API
- Amazon Titan Embeddings for vector embeddings
"""

import json
import boto3
import os
import logging
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

# Model IDs
# Text model: read from env so you can switch when AWS retires a version.
# In ap-south-1, Amazon Nova models are commonly available but require using an inference profile ID (e.g., "apac.amazon.nova-micro-v1:0").
# Titan Text model IDs have been frequently retired; prefer Nova inference profiles when available.
TEXT_MODEL_ID = os.getenv("TEXT_MODEL_ID", "apac.amazon.nova-micro-v1:0")
TITAN_EMBEDDING_MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v2:0")

# Embedding dimensions for Titan
# Titan Text Embeddings V2 commonly returns 1024 floats by default, but can vary by config.
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))


def get_embedding(text: str) -> List[float]:
    """
    Get embedding for a single text using Amazon Titan Embeddings.
    
    Args:
        text: Input text to embed (max 8192 tokens)
        
    Returns:
        List of floats representing the embedding vector (1536 dimensions)
    """
    try:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        logger.info(
            "Requesting Titan embedding with modelId=%s for text length=%d",
            TITAN_EMBEDDING_MODEL_ID,
            len(text),
        )

        body = json.dumps({"inputText": text})

        response = bedrock_runtime.invoke_model(
            modelId=TITAN_EMBEDDING_MODEL_ID,
            body=body,
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response["body"].read())

        if "embedding" not in response_body:
            raise ValueError("No embedding in response")

        embedding = response_body["embedding"]

        logger.info("Generated embedding vector of length %d", len(embedding))

        if EMBEDDING_DIMENSION and len(embedding) != EMBEDDING_DIMENSION:
            logger.warning(
                f"Unexpected embedding dimension: {len(embedding)}, expected {EMBEDDING_DIMENSION}. "
                "This may be fine if your embedding model/config uses a different vector size."
            )

        return embedding
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "AccessDeniedException":
            logger.error("Bedrock access denied. Ensure model access is granted.")
            raise Exception("Bedrock access denied. Please request model access in AWS Console.")
        raise Exception(f"Failed to get embedding: {str(e)}")
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings for multiple texts (sequential processing).
    
    Note: Titan doesn't support batch embeddings natively, so we process sequentially.
    For better performance, consider batching at the application level.
    
    Args:
        texts: List of input texts
        
    Returns:
        List of embedding vectors
    """
    embeddings: List[List[float]] = []
    for i, text in enumerate(texts):
        try:
            embedding = get_embedding(text)
            embeddings.append(embedding)
            logger.info(
                "Generated embedding for batch item %d (length=%d)",
                i,
                len(text or ""),
            )
            if (i + 1) % 10 == 0:
                logger.info("Processed %d/%d embeddings", i + 1, len(texts))
        except Exception as e:
            logger.error("Failed to embed text %d: %s", i, str(e))
            # Append empty embedding placeholder and continue
            embeddings.append([])
            continue

    return embeddings


def invoke_claude(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7
) -> str:
    """
    Invoke an LLM via Bedrock for text generation.

    Supports both:
    - Titan Text models (via InvokeModel API)
    - Nova models (via InvokeModel API - if model supports it, otherwise use inference profile)
    
    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        max_tokens: Maximum tokens to generate (default 4096)
        temperature: Sampling temperature (0.0-1.0, default 0.7)
        
    Returns:
        Generated text response
    """
    try:
        model_id = TEXT_MODEL_ID

        # If the chosen model is Nova (or an inference profile ARN), we should use Converse.
        # Nova often does NOT support on-demand InvokeModel with the Titan-style payload.
        looks_like_inference_profile = (
            model_id.startswith("arn:aws:bedrock:")
            or "inference-profile" in model_id
            or model_id.startswith("us.")  # cross-region inference profile IDs often look like this
        )
        is_nova = "nova" in model_id.lower()

        if looks_like_inference_profile or is_nova:
            # Use Converse API (preferred for Nova + inference profiles)
            if not hasattr(bedrock_runtime, "converse"):
                raise Exception("Your boto3 version does not support Bedrock Converse API. Please update boto3/botocore.")

            messages: List[Dict[str, Any]] = [{
                "role": "user",
                "content": [{"text": prompt}],
            }]
            system: Optional[List[Dict[str, Any]]] = None
            if system_prompt:
                system = [{"text": system_prompt}]

            response = bedrock_runtime.converse(
                modelId=model_id,
                messages=messages,
                system=system,
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature,
                    "topP": 0.9,
                },
            )

            output = response.get("output", {})
            message = output.get("message", {})
            content = message.get("content", [])
            if content and "text" in content[0]:
                return content[0]["text"]

            raise Exception("Empty response from text model")

        # Otherwise, default to InvokeModel (best for Titan Text)
        if system_prompt:
            full_prompt = f"{system_prompt.strip()}\n\nUser: {prompt.strip()}"
        else:
            full_prompt = prompt

        body = {
            "inputText": full_prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens,
                "temperature": temperature,
                "topP": 0.9,
            },
        }

        response = bedrock_runtime.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )

        response_body = json.loads(response["body"].read())

        if "results" in response_body and len(response_body["results"]) > 0 and "outputText" in response_body["results"][0]:
            return response_body["results"][0]["outputText"]
        if "outputText" in response_body:
            return response_body["outputText"]
        if "text" in response_body:
            return response_body["text"]

        raise Exception("Empty response from text model")
            
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        error_message = str(e)
        
        if error_code == "AccessDeniedException":
            logger.error("Bedrock access denied. Ensure Bedrock model access is granted.")
            raise Exception("Bedrock access denied. Please check your IAM permissions or Bedrock account settings.")
        if error_code == "ResourceNotFoundException" or "end of its life" in error_message.lower():
            logger.error(
                "Bedrock model not found or has been retired. "
                "Update TEXT_MODEL_ID/EMBEDDING_MODEL_ID environment variables to a valid Bedrock model ID."
            )
            raise Exception(
                "Bedrock model not found or retired. Please set TEXT_MODEL_ID to a valid Bedrock text model "
                "ID from the Model catalog in the AWS Console. For Nova models, you may need to use an inference profile ID."
            )
        if "inference profile" in error_message.lower():
            logger.error("Nova models require inference profiles. Use Titan Text or configure inference profile.")
            raise Exception(
                "Nova models require inference profiles. "
                "Set TEXT_MODEL_ID to an inference profile ID/ARN that contains Nova Micro/Lite, "
                "or switch TEXT_MODEL_ID to a Titan Text model (if available in your region)."
            )
        raise Exception(f"Failed to invoke text model: {str(e)}")
    except Exception as e:
        logger.error(f"Error invoking Claude: {str(e)}")
        raise


def format_rag_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
    """
    Format RAG prompt with retrieved context.
    
    Args:
        query: User query
        context_chunks: List of retrieved context chunks with metadata
        
    Returns:
        Formatted prompt string
    """
    if not context_chunks:
        return f"""Answer the following question about Indian government schemes and policies.

Question: {query}

If you don't know the answer, say so clearly."""
    
    context_text = "\n\n".join([
        f"[Source: {chunk.get('source', 'Unknown')}, Page: {chunk.get('page', 'N/A')}]\n{chunk.get('text', '')}"
        for chunk in context_chunks
    ])
    
    prompt = f"""You are a helpful AI assistant that provides accurate information about Indian government schemes and policies.

Use the following context to answer the user's question. If the context doesn't contain enough information, say so clearly.

Context:
{context_text}

User Question: {query}

Provide a clear, accurate answer based on the context above. Include citations to sources when relevant. If the context doesn't fully answer the question, acknowledge what information is missing."""
    
    return prompt
