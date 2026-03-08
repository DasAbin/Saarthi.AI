"""
Lambda handler for scheme recommendation based on user profile.

This handler matches users with relevant government schemes using:
- Amazon Bedrock (Claude 3 Sonnet) for intelligent matching
- User profile data (age, state, income, occupation)
"""

import json
import os
import sys
import logging
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.response import success_response, error_response, lambda_response
from utils.aws.bedrock import invoke_claude
from utils.data.schemes_db import SCHEMES_DATABASE, filter_schemes_by_profile
from utils.text_utils import parse_llm_json

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for scheme recommendation endpoint.
    
    Expected event body:
    {
        "age": 35,
        "state": "Maharashtra",
        "income": 200000,
        "occupation": "Farmer"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "schemes": [
                {
                    "name": "string",
                    "description": "string",
                    "eligibility": ["string"],
                    "apply_steps": ["string"],
                    "link": "string" (optional)
                }
            ]
        }
    }
    """
    try:
        logger.info("Scheme recommendation handler invoked")
        
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        
        # Validate inputs
        age = body.get("age")
        state = body.get("state", "").strip()
        income = body.get("income")
        occupation = body.get("occupation", "").strip()
        
        # Validation
        if not all([age, state, income is not None, occupation]):
            logger.warning("Missing required fields")
            return lambda_response(
                400,
                error_response("All fields (age, state, income, occupation) are required")
            )
        
        if not isinstance(age, int) or age < 1 or age > 120:
            return lambda_response(
                400,
                error_response("Age must be between 1 and 120")
            )
        
        if not isinstance(income, (int, float)) or income < 0:
            return lambda_response(
                400,
                error_response("Income must be a positive number")
            )
        
        logger.info(f"Processing recommendation for: age={age}, state={state}, income={income}, occupation={occupation}")
        
        # Step 1: Filter schemes by basic criteria
        filtered_schemes = filter_schemes_by_profile(age, income, occupation)
        logger.info(f"Found {len(filtered_schemes)} potentially matching schemes")
        
        if not filtered_schemes:
            # If no matches, use all schemes
            filtered_schemes = SCHEMES_DATABASE[:10]  # Limit to 10 for LLM processing
        
        # Step 2: Use Claude to intelligently match and rank schemes
        schemes_json = json.dumps(filtered_schemes, indent=2)
        
        prompt = f"""You are an expert at matching Indian citizens with relevant government schemes.

User Profile:
- Age: {age} years
- State: {state}
- Annual Income: ₹{income:,}
- Occupation: {occupation}

Available Schemes:
{schemes_json}

Based on the user profile, recommend the top 3 most relevant schemes. Consider:
1. Eligibility criteria match
2. Income level appropriateness
3. Age requirements
4. Occupation relevance
5. State-specific schemes if applicable

For each recommended scheme, provide:
- name: Exact scheme name
- description: Brief description (1-2 sentences)
- eligibility: List of eligibility criteria (as array)
- apply_steps: Step-by-step application process (as array)
- link: Official website link if available

Return ONLY a valid JSON array with this exact structure:
[
  {{
    "name": "Scheme Name",
    "description": "Brief description",
    "eligibility": ["criteria 1", "criteria 2"],
    "apply_steps": ["step 1", "step 2"],
    "link": "https://scheme-website.gov.in"
  }}
]

Return exactly 3 schemes, ranked by relevance."""
        
        system_prompt = (
            "You are an expert at matching citizens with government schemes. "
            "Provide accurate, helpful recommendations based on eligibility and user profile. "
            "Return only valid JSON, no additional text."
        )
        
        try:
            logger.info("Generating recommendations using Claude...")
            response_text = invoke_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.3  # Lower temperature for more consistent results
            )
            
            # Parse JSON from LLM response (handles fences, bracket scanning)
            schemes = parse_llm_json(response_text, fallback=None)
            if schemes is None:
                logger.warning("parse_llm_json returned None; using fallback schemes")
                schemes = [
                    {
                        "name": s["name"],
                        "description": s["description"],
                        "eligibility": s["eligibility"],
                        "apply_steps": s["apply_steps"],
                        "link": s.get("link"),
                    }
                    for s in filtered_schemes[:3]
                ]
            if not isinstance(schemes, list):
                schemes = [schemes]
            
            # Ensure we have exactly 3 schemes
            schemes = schemes[:3]
            
            # Validate scheme structure
            validated_schemes = []
            for scheme in schemes:
                if isinstance(scheme, dict) and "name" in scheme:
                    validated_schemes.append({
                        "name": scheme.get("name", "Unknown Scheme"),
                        "description": scheme.get("description", ""),
                        "eligibility": scheme.get("eligibility", []),
                        "apply_steps": scheme.get("apply_steps", []),
                        "link": scheme.get("link")
                    })
            
            if not validated_schemes:
                # Final fallback
                validated_schemes = [
                    {
                        "name": s["name"],
                        "description": s["description"],
                        "eligibility": s["eligibility"],
                        "apply_steps": s["apply_steps"],
                        "link": s.get("link")
                    }
                    for s in filtered_schemes[:3]
                ]
            
            logger.info(f"Returning {len(validated_schemes)} recommended schemes")
            
            return lambda_response(
                200,
                success_response({
                    "schemes": validated_schemes
                })
            )
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            # Fallback: return filtered schemes directly
            fallback_schemes = [
                {
                    "name": s["name"],
                    "description": s["description"],
                    "eligibility": s["eligibility"],
                    "apply_steps": s["apply_steps"],
                    "link": s.get("link")
                }
                for s in filtered_schemes[:3]
            ]
            
            return lambda_response(
                200,
                success_response({
                    "schemes": fallback_schemes
                })
            )
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return lambda_response(
            400,
            error_response("Invalid JSON in request body")
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return lambda_response(
            500,
            error_response(f"Internal server error: {str(e)}")
        )
