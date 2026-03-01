"""
Lambda handler for generating formal grievance/complaint letters.
"""

import json
import os
import sys
from typing import Dict, Any
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.bedrock_client import invoke_claude
from utils.response import success_response, error_response, lambda_response


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for grievance generation endpoint.
    
    Expected event body:
    {
        "issue_type": "Water Supply",
        "description": "No water supply for 3 days",
        "location": "Ward 5, Sector 12, City Name"
    }
    """
    try:
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        
        issue_type = body.get("issue_type", "").strip()
        description = body.get("description", "").strip()
        location = body.get("location", "").strip()
        
        if not all([issue_type, description, location]):
            return lambda_response(
                400,
                error_response("All fields (issue_type, description, location) are required")
            )
        
        # Generate complaint letter using Claude
        prompt = f"""Generate a formal complaint letter in English for a civic issue. The letter should be professional, clear, and include all relevant details.

Issue Type: {issue_type}
Description: {description}
Location: {location}
Date: {datetime.now().strftime("%B %d, %Y")}

The letter should:
1. Be addressed to the appropriate municipal authority
2. Include a clear subject line
3. Describe the issue in detail
4. Mention the location precisely
5. Request timely action
6. Include space for signature and contact details

Format it as a proper formal letter with:
- Date
- To address
- Subject
- Salutation
- Body paragraphs
- Closing
- Signature line
"""
        
        complaint_letter = invoke_claude(
            prompt=prompt,
            system_prompt="You are an expert at writing formal complaint letters to government authorities. Write clear, professional, and actionable letters.",
            max_tokens=2048,
            temperature=0.5
        )
        
        # Clean up the response (remove markdown formatting if present)
        if complaint_letter.startswith("```"):
            lines = complaint_letter.split("\n")
            complaint_letter = "\n".join(lines[1:-1]) if len(lines) > 2 else complaint_letter
        
        return lambda_response(
            200,
            success_response({
                "complaint_letter": complaint_letter
            })
        )
        
    except Exception as e:
        print(f"Error in grievance_handler: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return lambda_response(
            500,
            error_response(f"Internal server error: {str(e)}")
        )
