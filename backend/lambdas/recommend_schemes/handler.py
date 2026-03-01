"""
Lambda handler for scheme recommendation based on user profile.
"""

import json
import os
import sys
from typing import Dict, Any, List

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.bedrock_client import invoke_claude
from utils.response import success_response, error_response, lambda_response


# Sample scheme database (in production, this would be in a database)
SCHEMES_DB = [
    {
        "name": "Pradhan Mantri Awas Yojana (PMAY)",
        "description": "Housing scheme for economically weaker sections",
        "eligibility": ["Age 18+", "Annual income < ₹3 lakh", "No pucca house"],
        "apply_steps": ["Visit PMAY website", "Fill application form", "Submit documents", "Wait for approval"]
    },
    {
        "name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
        "description": "Direct income support to farmers",
        "eligibility": ["Farmer", "Landholding", "Age 18+"],
        "apply_steps": ["Visit PM-KISAN portal", "Register with Aadhaar", "Link bank account"]
    },
    {
        "name": "Ayushman Bharat",
        "description": "Health insurance for low-income families",
        "eligibility": ["Annual income < ₹5 lakh", "No existing health insurance"],
        "apply_steps": ["Check eligibility online", "Submit application", "Get health card"]
    },
    # Add more schemes...
]


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
    """
    try:
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        
        age = body.get("age")
        state = body.get("state", "").strip()
        income = body.get("income")
        occupation = body.get("occupation", "").strip()
        
        # Validate inputs
        if not all([age, state, income is not None, occupation]):
            return lambda_response(
                400,
                error_response("All fields (age, state, income, occupation) are required")
            )
        
        # Use Claude to match schemes
        prompt = f"""Based on the following user profile, recommend the top 3 most relevant Indian government schemes:

User Profile:
- Age: {age}
- State: {state}
- Annual Income: ₹{income:,}
- Occupation: {occupation}

Available Schemes:
{json.dumps(SCHEMES_DB, indent=2)}

For each recommended scheme, provide:
1. Scheme name
2. Description
3. Eligibility criteria (as a list)
4. Step-by-step application process (as a list)

Return the response as a JSON array with this structure:
[
  {{
    "name": "Scheme Name",
    "description": "Brief description",
    "eligibility": ["criteria 1", "criteria 2"],
    "apply_steps": ["step 1", "step 2"],
    "link": "https://scheme-website.gov.in" (if available)
  }}
]
"""
        
        response_text = invoke_claude(
            prompt=prompt,
            system_prompt="You are an expert at matching citizens with relevant government schemes. Provide accurate, helpful recommendations.",
            max_tokens=2048,
            temperature=0.3
        )
        
        # Parse JSON from response
        # Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        
        try:
            schemes = json.loads(response_text)
            if not isinstance(schemes, list):
                schemes = [schemes]
        except json.JSONDecodeError:
            # Fallback: return hardcoded recommendations
            schemes = SCHEMES_DB[:3]
        
        # Limit to top 3
        schemes = schemes[:3]
        
        return lambda_response(
            200,
            success_response({
                "schemes": schemes
            })
        )
        
    except Exception as e:
        print(f"Error in recommend_schemes handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return lambda_response(
            500,
            error_response(f"Internal server error: {str(e)}")
        )
