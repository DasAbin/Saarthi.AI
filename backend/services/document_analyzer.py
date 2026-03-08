from __future__ import annotations

"""
High-level document analysis service.

Takes cleaned document text and uses Bedrock (Nova / Titan via invoke_claude)
to produce a structured analysis suitable for the frontend.
"""

import json
import logging
from typing import Any, Dict, List

from utils.aws.bedrock import invoke_claude

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


SYSTEM_PROMPT = (
    "You are an expert policy analyst AI that analyzes government documents and "
    "produces structured intelligence reports for public service applications."
)


def _build_prompt(text: str) -> str:
    return (
        "You are an expert policy analyst AI.\n\n"
        "Analyze the extracted document and produce a structured intelligence report.\n\n"
        "Focus on:\n"
        "* Key policy facts\n"
        "* Eligibility criteria\n"
        "* Healthcare benefits\n"
        "* Operational workflows\n"
        "* Stakeholder roles\n"
        "* Community impact\n"
        "* Important contacts\n"
        "* Frequently asked questions\n"
        "* Insights useful for government or public service applications\n\n"
        "Return the response strictly in JSON using the following schema:\n\n"
        "{\n"
        '  "document_overview": "2-4 sentence overview of the document",\n'
        '  "scheme_facts": {\n'
        '    "scheme_name": "name of the scheme or program",\n'
        '    "coverage_amount": "financial coverage or benefit amount if applicable",\n'
        '    "launch_year": "year the scheme was launched if mentioned",\n'
        '    "beneficiaries": "target beneficiary description",\n'
        '    "target_population": "who this document/scheme is for",\n'
        '    "institution": "government body or institution responsible"\n'
        "  },\n"
        '  "eligibility_and_coverage": ["array of eligibility criteria and coverage details"],\n'
        '  "healthcare_benefits": ["array of healthcare benefits or services covered"],\n'
        '  "operational_workflow": ["array of step-by-step operational procedures"],\n'
        '  "stakeholders_and_roles": [\n'
        "    {\n"
        '      "role": "stakeholder role name",\n'
        '      "responsibilities": ["array of responsibilities for this role"]\n'
        "    }\n"
        "  ],\n"
        '  "community_impact": ["array of community impact points"],\n'
        '  "policy_insights": ["array of 4-6 concise policy insights, implications, or recommendations"],\n'
        '  "key_contacts": [\n'
        "    {\n"
        '      "service": "service or department name",\n'
        '      "contact": "contact information (phone, email, helpline, etc.)"\n'
        "    }\n"
        "  ],\n"
        '  "frequently_asked_questions": [\n'
        "    {\n"
        '      "question": "common question",\n'
        '      "answer": "concise answer"\n'
        "    }\n"
        "  ],\n"
        '  "summary": "comprehensive summary (8-12 sentences) in plain language"\n'
        "}\n\n"
        "Important:\n"
        "- If a section is not applicable or not found in the document, return an empty array [] or empty string \"\"\n"
        "- Do not make up information that is not in the document\n"
        "- The JSON must be the ONLY thing in your reply. No markdown, no explanations outside the JSON.\n\n"
        "Document Text:\n"
        f"{text}\n"
    )


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


def analyze_document(text: str) -> Dict[str, Any]:
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

        return {
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

    except Exception as e:
        logger.error("Document analysis failed: %s", str(e), exc_info=True)
        # Fallback: simple heuristic summary
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        summary = ". ".join(sentences[:8])
        if summary and not summary.endswith("."):
            summary += "."

        return {
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

