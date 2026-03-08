import json
import logging
import re
from typing import Iterable

from django.conf import settings

logger = logging.getLogger("nexalix_app.chatbot")


FALLBACK_SERVICE_HINTS = {
    "ai": ["AI Solutions", "Data Analytics"],
    "automation": ["Software Development", "Cloud & Infrastructure"],
    "cloud": ["Cloud & Infrastructure", "IT Consulting"],
    "data": ["Data Analytics", "AI Solutions"],
    "analytics": ["Data Analytics", "AI Solutions"],
    "website": ["Software Development", "Digital Transformation"],
    "mobile": ["Software Development", "Digital Transformation"],
    "security": ["IT Consulting", "Cloud & Infrastructure"],
    "quote": ["Auto Quote Generator", "IT Consulting"],
    "pricing": ["Auto Quote Generator", "IT Consulting"],
}


def _clean_text(value: str, *, limit: int = 6000) -> str:
    value = (value or "").strip()
    return value[:limit]


def _normalize_services(services: Iterable) -> list[dict]:
    normalized = []
    for service in services:
        normalized.append(
            {
                "title": getattr(service, "title", "").strip(),
                "category": getattr(service, "get_category_display", lambda: "")(),
                "summary": _clean_text(getattr(service, "short_description", ""), limit=220),
                "pricing": _clean_text(getattr(service, "pricing_info", ""), limit=180),
            }
        )
    return [item for item in normalized if item["title"]]


def _build_service_catalog(services: list[dict]) -> str:
    if not services:
        return "No service catalog found in database."

    rows = []
    for item in services:
        lines = [f"- {item['title']} ({item['category'] or 'General'})"]
        if item["summary"]:
            lines.append(f"  Summary: {item['summary']}")
        if item["pricing"]:
            lines.append(f"  Pricing hint: {item['pricing']}")
        rows.append("\n".join(lines))
    return "\n".join(rows)


def _extract_json_payload(raw_content: str) -> dict:
    raw_content = (raw_content or "").strip()
    if not raw_content:
        return {}

    try:
        return json.loads(raw_content)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw_content, re.DOTALL)
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def _fallback_recommendations(user_message: str) -> list[str]:
    text = (user_message or "").lower()
    picks = []
    for key, services in FALLBACK_SERVICE_HINTS.items():
        if key in text:
            picks.extend(services)
    seen = set()
    ordered = []
    for item in picks:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered[:3]


def build_fallback_response(user_message: str, whatsapp_url: str, contact_url: str, quote_url: str) -> dict:
    recommendations = _fallback_recommendations(user_message)

    answer = (
        "I can help with Nexalix consulting services, project scoping, and quote guidance. "
        f"For pricing direction, use the quote tool: {quote_url}. "
        "If you share your goals, timeline, and budget range, I can recommend the best service path."
    )

    collect_lead = any(keyword in (user_message or "").lower() for keyword in ["contact", "quote", "proposal", "call", "project"])

    return {
        "answer": answer,
        "recommended_services": recommendations,
        "collect_lead": collect_lead,
        "escalate_to_human": collect_lead,
        "escalation_message": (
            f"Need a fast response? Reach us on WhatsApp: {whatsapp_url} "
            f"or submit details here: {contact_url}"
        ),
    }


def generate_chatbot_response(
    *,
    user_message: str,
    history: list[dict],
    services: Iterable,
    quote_url: str,
    contact_url: str,
    whatsapp_url: str,
) -> dict:
    """Generate chatbot output using OpenAI, with deterministic fallback on failure."""
    message = _clean_text(user_message, limit=1200)
    if not message:
        return {
            "answer": "Please share a question or brief project goal so I can help.",
            "recommended_services": [],
            "collect_lead": False,
            "escalate_to_human": False,
            "escalation_message": "",
        }

    service_rows = _normalize_services(services)
    service_catalog = _build_service_catalog(service_rows)

    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY missing. Falling back to static chatbot response.")
        return build_fallback_response(message, whatsapp_url, contact_url, quote_url)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        system_prompt = f"""
You are Nexalix's website assistant.

Objectives:
1) Answer visitor questions about Nexalix services.
2) Explain quote/pricing process clearly.
3) Recommend relevant services from available catalog.
4) Encourage lead capture when user has project intent.
5) Offer escalation to human support via WhatsApp/contact page where needed.

Company service catalog:
{service_catalog}

Quote flow:
- Visitor can use the Auto Quote Generator at {quote_url}.
- For final pricing, ask for scope, complexity, timeline, integrations, and support requirements.

Style rules:
- Be concise and professional.
- Do not invent services outside catalog unless very generic.
- If unsure, ask one focused follow-up question.

Return ONLY valid JSON with this exact structure:
{{
  "answer": "string",
  "recommended_services": ["service1", "service2"],
  "collect_lead": true_or_false,
  "escalate_to_human": true_or_false,
  "escalation_message": "string"
}}
""".strip()

        safe_history = []
        for item in history[-12:]:
            role = item.get("role")
            content = _clean_text(item.get("content", ""), limit=1000)
            if role in {"user", "assistant"} and content:
                safe_history.append({"role": role, "content": content})

        messages = [{"role": "system", "content": system_prompt}, *safe_history, {"role": "user", "content": message}]

        completion = client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=messages,
            temperature=settings.OPENAI_CHAT_TEMPERATURE,
            max_tokens=settings.OPENAI_CHAT_MAX_TOKENS,
            response_format={"type": "json_object"},
        )

        raw_content = completion.choices[0].message.content if completion.choices else ""
        payload = _extract_json_payload(raw_content)

        answer = _clean_text(str(payload.get("answer", "")), limit=2500)
        if not answer:
            return build_fallback_response(message, whatsapp_url, contact_url, quote_url)

        recommended_services = payload.get("recommended_services") or []
        if isinstance(recommended_services, str):
            recommended_services = [recommended_services]
        if not isinstance(recommended_services, list):
            recommended_services = []
        recommended_services = [
            _clean_text(str(item), limit=80)
            for item in recommended_services
            if _clean_text(str(item), limit=80)
        ][:4]

        collect_lead = bool(payload.get("collect_lead"))
        escalate = bool(payload.get("escalate_to_human"))

        escalation_message = _clean_text(str(payload.get("escalation_message", "")), limit=300)
        if not escalation_message and (escalate or collect_lead):
            escalation_message = (
                f"Need direct support? WhatsApp us: {whatsapp_url} "
                f"or contact us here: {contact_url}"
            )

        return {
            "answer": answer,
            "recommended_services": recommended_services,
            "collect_lead": collect_lead,
            "escalate_to_human": escalate,
            "escalation_message": escalation_message,
        }

    except Exception as exc:
        logger.exception("Chatbot OpenAI request failed: %s", exc)
        return build_fallback_response(message, whatsapp_url, contact_url, quote_url)
