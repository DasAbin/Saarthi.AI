"""
Lambda handler for generating formal grievance/complaint letters.

This handler generates formal complaint letters using:
- Amazon Bedrock (Claude 3 Sonnet) for letter generation
- User-provided issue details
- Multilingual support based on user preference
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
from utils.text_utils import sanitize_text

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
        "location": "Ward 5, Sector 12, City Name",
        "language": "en" | "hi" | "mr" (optional, default "en")
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
        language = body.get("language", "en").strip().lower()
        
        if language not in ["en", "hi", "mr"]:
            language = "en"
            
        if not all([issue_type, description, location]):
            logger.warning("Missing required fields")
            return lambda_response(
                400,
                error_response("All fields (issue_type, description, location) are required")
            )
        
        logger.info(f"Generating complaint letter for: {issue_type} at {location} in {language}")
        
        # Format prompt for complaint letter generation
        current_date = datetime.now().strftime("%B %d, %Y")
        
        language_instructions = {
            "en": "Generate a formal, professional complaint letter in English",
            "hi": "कृपया यह शिकायत पत्र हिंदी (Hindi) में लिखें। एक औपचारिक और पेशेवर शिकायत पत्र तैयार करें।",
            "mr": "कृपया हे तक्रार पत्र मराठीत (Marathi) लिहा। एक औपचारिक आणि व्यावसायिक तक्रार पत्र तयार करा।"
        }
        
        prompt = f"""{language_instructions[language]} to the appropriate municipal authority for a civic issue.

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
            "remain respectful and clear. Always respond strictly in the requested language."
        )
        
        try:
            logger.info("Generating complaint letter using Claude...")
            complaint_letter = invoke_claude(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=2048,
                temperature=0.5
            )
            
            # Clean up the response — strip control characters and markdown fences
            cleaned_letter = sanitize_text(complaint_letter.strip(), max_length=8000)

            # Strip bare ``` fences if the LLM wrapped the letter
            if cleaned_letter.startswith("```"):
                lines = cleaned_letter.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned_letter = "\n".join(lines).strip()
            
            # Ensure proper formatting depending on language
            date_prefix = {
                "en": "Date:",
                "hi": "दिनांक:",
                "mr": "दिनांक:"
            }
            if not cleaned_letter.startswith(date_prefix[language]) and not cleaned_letter.startswith("Date:"):
                # Add date if missing
                cleaned_letter = f"{date_prefix[language]} {current_date}\n\n{cleaned_letter}"
            
            logger.info(f"Generated complaint letter: {len(cleaned_letter)} characters")
            
            return lambda_response(
                200,
                success_response({
                    "complaint_letter": cleaned_letter
                })
            )
            
        except Exception as e:
            logger.error(f"Error generating complaint letter: {str(e)}")
            # Fallback based on language
            fallback_letters = {
                "en": f"""Date: {current_date}

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
[Your Email Address]""",
                
                "hi": f"""दिनांक: {current_date}

प्रति,
नगर निगम अधिकारी,
{location}

विषय: {issue_type} के संबंध में शिकायत

महोदय/महोदया,

मैं आपका ध्यान निम्नलिखित समस्या की ओर आकर्षित करना चाहता/चाहती हूँ:

{description}

स्थान: {location}

इस समस्या के कारण काफी असुविधा हो रही है और इस पर तत्काल ध्यान देने की आवश्यकता है। मेरा आपसे अनुरोध है कि कृपया इस मामले को जल्द से जल्द सुलझाने के लिए आवश्यक कार्रवाई करें।

मैं आपकी त्वरित प्रतिक्रिया और कार्रवाई की प्रतीक्षा कर रहा/रही हूँ।

सहयोग के लिए धन्यवाद।

भवदीय,

[आपका नाम]
[आपका पता]
[आपका संपर्क नंबर]
[आपका ईमेल]""",

                "mr": f"""दिनांक: {current_date}

प्रति,
महानगरपालिका अधिकारी,
{location}

विषय: {issue_type} बाबत तक्रार

महोदय/महोदया,

मी खालील समस्येकडे आपले लक्ष वेधून घेऊ इच्छितो/इच्छिते:

{description}

ठिकाण: {location}

या समस्येमुळे खूप गैरसोय होत आहे आणि याकडे तातडीने लक्ष देण्याची गरज आहे. माझी आपणास विनंती आहे की कृपया ही समस्या लवकरात लवकर सोडवण्यासाठी आवश्यक ती कारवाई करावी.

मी आपल्या त्वरित प्रतिसादाची आणि कारवाईची वाट पाहत आहे.

सहकार्याबद्दल धन्यवाद.

आपला/आपली नम्र,

[तुमचे नाव]
[तुमचा पत्ता]
[तुमचा संपर्क क्रमांक]
[तुमचा ईमेल]"""
            }
            
            return lambda_response(
                200,
                success_response({
                    "complaint_letter": fallback_letters.get(language, fallback_letters["en"])
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
