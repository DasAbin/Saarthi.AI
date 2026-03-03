"""
Text summarization utilities using Bedrock Claude.
"""

import logging
from typing import List, Dict, Any

from utils.aws.bedrock import invoke_claude

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def generate_summary(text: str, max_length: int = 2000) -> str:
    """
    Generate a concise summary of the text.
    
    Args:
        text: Input text to summarize
        max_length: Maximum length of summary (characters)
        
    Returns:
        Summary text
    """
    try:
        # Truncate text if too long (to avoid token limits)
        # Claude 3 Sonnet can handle ~200k tokens, but we'll limit to ~8000 chars for safety
        text_preview = text[:8000] if len(text) > 8000 else text
        
        prompt = f"""Summarize the following government policy document. Provide a clear, concise summary (2-3 paragraphs) that captures the main points, important dates, eligibility criteria, and key information.

Document text:
{text_preview}

Summary:"""
        
        system_prompt = (
            "You are an expert at summarizing government policy documents. "
            "Extract key information clearly and concisely. Focus on: "
            "main objectives, eligibility criteria, important dates/deadlines, "
            "application process, and benefits."
        )
        
        summary = invoke_claude(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=1024,
            temperature=0.3  # Lower temperature for more factual summaries
        )
        
        # Limit summary length
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        logger.info(f"Generated summary: {len(summary)} characters")
        return summary.strip()
        
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise


def extract_key_points(text: str, max_points: int = 7) -> List[str]:
    """
    Extract key points from text as a bulleted list.
    
    Args:
        text: Input text
        max_points: Maximum number of key points
        
    Returns:
        List of key point strings
    """
    try:
        # Truncate text if too long
        text_preview = text[:6000] if len(text) > 6000 else text
        
        prompt = f"""Extract {max_points} key points from this government policy document. Return only a bulleted list, one point per line. Focus on:
- Important eligibility criteria
- Key dates or deadlines
- Main benefits or features
- Application requirements
- Important restrictions or conditions

Document text:
{text_preview}

Key Points:"""
        
        system_prompt = (
            "You are an expert at extracting key information from government documents. "
            "Return only a bulleted list of the most important points. "
            "Each point should be concise (1-2 sentences)."
        )
        
        response = invoke_claude(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=512,
            temperature=0.3
        )
        
        # Parse bullet points
        points = []
        for line in response.split("\n"):
            line = line.strip()
            if not line:
                continue
            
            # Remove bullet markers
            for marker in ["-", "•", "*", "1.", "2.", "3.", "4.", "5.", "6.", "7."]:
                if line.startswith(marker):
                    line = line[len(marker):].strip()
                    break
            
            if line and len(line) > 10:  # Filter out very short lines
                points.append(line)
        
        # Limit to max_points
        points = points[:max_points]
        
        logger.info(f"Extracted {len(points)} key points")
        return points
        
    except Exception as e:
        logger.error(f"Error extracting key points: {str(e)}")
        # Fallback: return empty list or simple extraction
        return []


def extract_structured_info(text: str) -> Dict[str, Any]:
    """
    Extract structured information from document (dates, amounts, etc.).
    
    Args:
        text: Input text
        
    Returns:
        Dictionary with structured information
    """
    try:
        text_preview = text[:4000] if len(text) > 4000 else text
        
        prompt = f"""Extract structured information from this government policy document. Return a JSON object with:
- scheme_name: Name of the scheme/program
- eligibility_age: Age requirements if mentioned
- eligibility_income: Income requirements if mentioned
- application_deadline: Deadline if mentioned
- benefits: Main benefits offered
- contact_info: Contact information if available

Document text:
{text_preview}

Return only valid JSON:"""
        
        system_prompt = "You are an expert at extracting structured information. Return only valid JSON."
        
        response = invoke_claude(
            prompt=prompt,
            system_prompt=system_prompt,
            max_tokens=512,
            temperature=0.2
        )
        
        # Try to parse JSON
        import json
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            structured_info = json.loads(cleaned)
            return structured_info
        except json.JSONDecodeError:
            logger.warning("Could not parse structured info as JSON")
            return {}
        
    except Exception as e:
        logger.error(f"Error extracting structured info: {str(e)}")
        return {}
