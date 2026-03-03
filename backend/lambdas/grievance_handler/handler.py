"""
Lambda handler for generating formal grievance/complaint letters.

This handler generates formal complaint letters using:
- Amazon Bedrock (Claude 3 Sonnet) for letter generation
- User-provided issue details
"""

import json
import os
import sys
import logging
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from utils.response import success_response, error_response, lambda_response
from utils.aws.bedrock import invoke_claude

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for grievance generation endpoint.
    
    Expected event body:
    {
        "issue_type": "Water Supply",
        "description": "No water supply for 3 days",
        "location": "Ward 5, Sector 12, City Name"
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "complaint_letter": "formatted complaint letter text"
        }
    }
    """
    try:
        logger.info("Grievance handler invoked")
        
        # Parse request body
        if isinstance(event.get("body"), str):
            body = json.loads(event["body"])
        else:
            body = event.get("body", {})
        
        # Validate inputs
        issue_type = body.get("issue_type", "").strip()
        description = body.get("description", "").strip()
        location = body.get("location", "").strip()
        
        if not all([issue_type, description, location]):
            logger.warning("Missing required fields")
            return lambda_response(
                400,
                error_response("All fields (issue_type, description, location) are required")
            )
        
        logger.info(f"Generating complaint letter for: {issue_type} at {location}")
        
        # Format prompt for complaint letter generation
        current_date = datetime.now().strftime("%B %d, %Y")
        
        prompt = f"""Generate a formal, professional complaint letter in English for a civic issue to the appropriate municipal authority.

Issue Details:
- Issue Type: {issue_type}
- Description: {description}
- Location: {location}
- Date: {current_date}

The letter should:
1. Be properly formatted with date, to address, subject, salutation
2. Clearly describe the issue and its impact
3. Mention the exact location with details
4. Request timely action
5. Be professional, respectful, and formal
6. Include space for signature and contact details at the end
7. Follow standard government letter format

Format the letter as a complete, ready-to-use complaint letter."""
        
        system_prompt = (
            "You are an expert at writing formal complaint letters to government authorities. "
            "Write clear, professional, and actionable letters that follow standard government "
            "letter format. Be specific about the issue and location. Use formal language but "
            "remain respectful and clear."
        )
        
        try:
            logger.info("Generating complaint letter using Claude...")
            complaint_letter = invoke_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.5
            )
            
            # Clean up the response (remove markdown formatting if present)
            cleaned_letter = complaint_letter.strip()
            
            # Remove markdown code blocks if present
            if cleaned_letter.startswith("```"):
                lines = cleaned_letter.split("\n")
                # Remove first and last line if they are code block markers
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned_letter = "\n".join(lines)
            
            # Ensure proper formatting
            if not cleaned_letter.startswith("Date:"):
                # Add date if missing
                cleaned_letter = f"Date: {current_date}\n\n{cleaned_letter}"
            
            logger.info(f"Generated complaint letter: {len(cleaned_letter)} characters")
            
            return lambda_response(
                200,
                success_response({
                    "complaint_letter": cleaned_letter
                })
            )
            
        except Exception as e:
            logger.error(f"Error generating complaint letter: {str(e)}")
            # Fallback: Generate basic letter template
            fallback_letter = f"""Date: {current_date}

To,
The Municipal Authority,
{location}

Subject: Complaint regarding {issue_type}

Dear Sir/Madam,

I am writing to bring to your attention the following issue:

{description}

Location: {location}

This issue has been causing inconvenience and needs immediate attention. I request your office to take necessary action to resolve this matter at the earliest.

I look forward to your prompt response and action.

Thank you for your cooperation.

Yours sincerely,

[Your Name]
[Your Address]
[Your Contact Number]
[Your Email Address]"""
            
            return lambda_response(
                200,
                success_response({
                    "complaint_letter": fallback_letter
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
