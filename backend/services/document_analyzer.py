from __future__ import annotations

"""
High-level document analysis service.

Takes cleaned document text and uses Bedrock (Nova / Titan via invoke_claude)
to produce a structured analysis suitable for the frontend.
"""

import json
import logging
from typing import Any, Dict, List

import boto3

from utils.aws.bedrock import invoke_claude

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# AWS Translate client (region inherited from environment/AWS config)
translate = boto3.client("translate")


SYSTEM_PROMPT = (
    "You are an expert government policy analyst that analyzes official documents "
    "and produces detailed, structured intelligence reports for public service applications."
)


def _build_prompt(text: str) -> str:
    prompt = f"""
You are an expert government policy analyst.

Analyze the following government document and generate a detailed structured analysis.

Document Text:
{text}

Generate the following sections:

1. Document Overview
   Write a detailed explanation (120–150 words) describing the purpose of the document,
   its scope, and what the document is trying to achieve.

2. Summary
   Generate a detailed and informative summary (150–250 words).
   
   The summary should include:
   
   • What the scheme/document is about
   • Who it benefits
   • Key features and coverage
   • Operational structure or workflow
   • Why it matters for society or public policy
   
   The summary should be written clearly so that a reader can understand the entire document without reading the original PDF.
   
   Avoid repeating bullet points. Write a structured paragraph explanation.

3. Scheme Facts (REQUIRED)
   Extract the following structured scheme information if present in the document:
   
   {{
     "scheme_name": "",
     "launch_year": "",
     "coverage_amount": "",
     "beneficiaries": "",
     "target_population": "",
     "institution": ""
   }}
   
   Rules:
   * If the document clearly mentions the scheme name, populate scheme_name.
   * If launch year is mentioned, populate launch_year.
   * If coverage amount like ₹5 lakh is mentioned, populate coverage_amount.
   * If the scheme serves a specific number of beneficiaries, populate beneficiaries.
   * If the document targets poor families or a defined group, populate target_population.
   * If a ministry or government body runs the scheme, populate institution.
   
   IMPORTANT: Always include scheme_facts in your response, even if some fields are empty.
   Extract all available information from the document.

4. Community Impact
   Provide 4–6 bullet points explaining how the scheme or policy benefits citizens.

5. Policy Insights
   Provide 4–6 key insights about implementation, governance, and policy significance.

6. Eligibility and Coverage
   Extract eligibility conditions and benefits.

7. Operational Workflow
   Describe step-by-step how the scheme operates.

8. Key Contacts
   Extract phone numbers, emails, and organizations mentioned.

Return the result strictly as JSON with keys:

document_overview
summary
scheme_facts
community_impact
policy_insights
eligibility_and_coverage
operational_workflow
key_contacts
"""
    return prompt


def _ensure_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        # Split on newlines or numbered bullets if the model returned plain text
        parts = [p.strip("-• ").strip() for p in value.splitlines() if p.strip()]
        if parts:
            return parts
    return []


def _ensure_dict(value: Any, default: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure value is a dictionary with required keys."""
    if isinstance(value, dict):
        result = {}
        for key in default.keys():
            result[key] = value.get(key, default[key])
        return result
    return default


def _ensure_stakeholder_list(value: Any) -> List[Dict[str, Any]]:
    """Ensure value is a list of stakeholder objects."""
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, dict):
            role = str(item.get("role", "")).strip()
            responsibilities = _ensure_list(item.get("responsibilities", []))
            if role:
                result.append({"role": role, "responsibilities": responsibilities})
    return result


def _ensure_contact_list(value: Any) -> List[Dict[str, Any]]:
    """Ensure value is a list of contact objects."""
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, dict):
            service = str(item.get("service", "")).strip()
            contact = str(item.get("contact", "")).strip()
            if service or contact:
                result.append({"service": service, "contact": contact})
    return result


def _ensure_faq_list(value: Any) -> List[Dict[str, Any]]:
    """Ensure value is a list of FAQ objects."""
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if isinstance(item, dict):
            question = str(item.get("question", "")).strip()
            answer = str(item.get("answer", "")).strip()
            if question or answer:
                result.append({"question": question, "answer": answer})
    return result


SUPPORTED_LANGUAGES = {
    "en",
    "hi",
    "mr",
    "ta",
    "te",
    "bn",
    "gu",
    "kn",
    "ml",
    "pa",
}


def translate_text(text: str, target_language: str) -> str:
    """
    Translate text from English to the target language using AWS Translate.
    """
    if not text or target_language == "en":
        return text

    if target_language not in SUPPORTED_LANGUAGES:
        logger.warning("Unsupported target language for translation: %s", target_language)
        return text

    try:
        response = translate.translate_text(
            Text=text,
            SourceLanguageCode="en",
            TargetLanguageCode=target_language,
        )
        return response.get("TranslatedText", text)
    except Exception as e:
        logger.error("Translation failed for language=%s: %s", target_language, str(e), exc_info=True)
        return text


def analyze_document(text: str, language: str = "en") -> Dict[str, Any]:
    """
    Analyze a cleaned document and return structured intelligence report with:
    - document_overview
    - scheme_facts
    - eligibility_and_coverage
    - healthcare_benefits
    - operational_workflow
    - stakeholders_and_roles
    - community_impact
    - policy_insights
    - key_contacts
    - frequently_asked_questions
    - summary
    """
    if not text:
        return {
            "document_overview": "",
            "scheme_facts": {
                "scheme_name": "",
                "coverage_amount": "",
                "launch_year": "",
                "beneficiaries": "",
                "target_population": "",
                "institution": "",
            },
            "eligibility_and_coverage": [],
            "healthcare_benefits": [],
            "operational_workflow": [],
            "stakeholders_and_roles": [],
            "community_impact": [],
            "policy_insights": [],
            "key_contacts": [],
            "frequently_asked_questions": [],
            "summary": "",
        }

    prompt = _build_prompt(text)

    try:
        # Keep analysis latency low: limit max_tokens so we stay under API Gateway limits
        # Using 1000 tokens to ensure we stay under 29s (Textract takes ~24-25s, leaving ~4-5s for Bedrock)
        logger.info("Invoking Bedrock for document analysis (text length=%d)", len(text))
        raw = invoke_claude(prompt, system_prompt=SYSTEM_PROMPT, max_tokens=1000)
        logger.debug("Raw document analysis response: %s", raw[:500])

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Model did not return valid JSON; attempting to recover.")
            # Try to find JSON object inside the string
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                data = json.loads(raw[start : end + 1])
            else:
                raise

        # Extract all fields with graceful fallbacks
        document_overview = str(data.get("document_overview", "")).strip()
        
        scheme_facts_default = {
            "scheme_name": "",
            "coverage_amount": "",
            "launch_year": "",
            "beneficiaries": "",
            "target_population": "",
            "institution": "",
        }
        scheme_facts = _ensure_dict(data.get("scheme_facts", {}), scheme_facts_default)
        
        eligibility_and_coverage = _ensure_list(data.get("eligibility_and_coverage", []))
        healthcare_benefits = _ensure_list(data.get("healthcare_benefits", []))
        operational_workflow = _ensure_list(data.get("operational_workflow", []))
        stakeholders_and_roles = _ensure_stakeholder_list(data.get("stakeholders_and_roles", []))
        community_impact = _ensure_list(data.get("community_impact", []))
        policy_insights = _ensure_list(data.get("policy_insights", []))
        key_contacts = _ensure_contact_list(data.get("key_contacts", []))
        frequently_asked_questions = _ensure_faq_list(data.get("frequently_asked_questions", []))
        summary = str(data.get("summary", "")).strip()

        analysis: Dict[str, Any] = {
            "document_overview": document_overview,
            "scheme_facts": scheme_facts,
            "eligibility_and_coverage": eligibility_and_coverage,
            "healthcare_benefits": healthcare_benefits,
            "operational_workflow": operational_workflow,
            "stakeholders_and_roles": stakeholders_and_roles,
            "community_impact": community_impact,
            "policy_insights": policy_insights,
            "key_contacts": key_contacts,
            "frequently_asked_questions": frequently_asked_questions,
            "summary": summary,
        }

        # Apply translation if requested and supported
        if language and language != "en":
            logger.info("Translating analysis to language=%s using AWS Translate", language)
            try:
                analysis["document_overview"] = translate_text(
                    analysis.get("document_overview", ""), language
                )
                analysis["summary"] = translate_text(
                    analysis.get("summary", ""), language
                )
                analysis["community_impact"] = [
                    translate_text(item, language)
                    for item in analysis.get("community_impact", [])
                ]
                analysis["policy_insights"] = [
                    translate_text(item, language)
                    for item in analysis.get("policy_insights", [])
                ]
                analysis["eligibility_and_coverage"] = [
                    translate_text(item, language)
                    for item in analysis.get("eligibility_and_coverage", [])
                ]
                analysis["operational_workflow"] = [
                    translate_text(item, language)
                    for item in analysis.get("operational_workflow", [])
                ]
            except Exception as e:
                logger.error("Failed to translate analysis to language=%s: %s", language, str(e), exc_info=True)

        return analysis

    except Exception as e:
        logger.error("Document analysis failed: %s", str(e), exc_info=True)
        # Fallback: simple heuristic summary
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        summary = ". ".join(sentences[:8])
        if summary and not summary.endswith("."):
            summary += "."

        analysis: Dict[str, Any] = {
            "document_overview": summary[:200] if summary else "",
            "scheme_facts": {
                "scheme_name": "",
                "coverage_amount": "",
                "launch_year": "",
                "beneficiaries": "",
                "target_population": "",
                "institution": "",
            },
            "eligibility_and_coverage": sentences[:3] if sentences else [],
            "healthcare_benefits": [],
            "operational_workflow": [],
            "stakeholders_and_roles": [],
            "community_impact": [],
            "policy_insights": [],
            "key_contacts": [],
            "frequently_asked_questions": [],
            "summary": summary or text[:500],
        }

        # Translate fallback analysis if a non-English language is requested
        if language and language != "en":
            logger.info("Translating fallback analysis to language=%s using AWS Translate", language)
            try:
                analysis["document_overview"] = translate_text(
                    analysis.get("document_overview", ""), language
                )
                analysis["summary"] = translate_text(
                    analysis.get("summary", ""), language
                )
                analysis["eligibility_and_coverage"] = [
                    translate_text(item, language)
                    for item in analysis.get("eligibility_and_coverage", [])
                ]
            except Exception as e:
                logger.error("Failed to translate fallback analysis to language=%s: %s", language, str(e), exc_info=True)

        return analysis

