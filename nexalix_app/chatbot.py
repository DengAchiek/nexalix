import json
import logging
import re
from typing import Iterable

from django.conf import settings

from .chatbot_knowledge import CHATBOT_CONFIG, COMPANY_PROFILE, FAQ_EXAMPLES, INTENTS

logger = logging.getLogger("nexalix_app.chatbot")


FALLBACK_SERVICE_HINTS = {
    "ai": ["AI Solutions", "Machine Learning"],
    "automation": ["Automation Systems", "Software Development"],
    "cloud": ["Technology Consulting", "Software Development"],
    "data": ["Data Analytics", "Machine Learning"],
    "analytics": ["Data Analytics", "AI Solutions"],
    "website": ["Software Development", "Technology Consulting"],
    "mobile": ["Software Development", "Technology Consulting"],
    "security": ["Technology Consulting", "Software Development"],
    "quote": ["Technology Consulting", "Software Development"],
    "pricing": ["Technology Consulting", "Software Development"],
}


INTENT_SERVICE_MAP = {
    "company_overview": ["Software Development", "AI Solutions", "Technology Consulting"],
    "industries_served": ["Technology Consulting", "Data Analytics"],
    "business_help": ["Automation Systems", "Data Analytics", "Software Development"],
    "custom_software": ["Software Development"],
    "software_technologies": ["Software Development"],
    "upgrade_existing_system": ["Software Development", "Technology Consulting"],
    "ai_solutions": ["AI Solutions", "Machine Learning"],
    "types_of_ai_systems": ["AI Solutions", "Machine Learning"],
    "ai_business_value": ["AI Solutions", "Data Analytics"],
    "machine_learning_explained": ["Machine Learning", "Data Analytics"],
    "predictive_models": ["Machine Learning", "Data Analytics"],
    "ml_efficiency": ["Machine Learning", "Automation Systems"],
    "data_analytics": ["Data Analytics"],
    "analytics_services": ["Data Analytics", "Machine Learning"],
    "dashboards": ["Data Analytics", "Software Development"],
    "automation_systems": ["Automation Systems", "Software Development"],
    "automation_benefits": ["Automation Systems"],
    "technology_consulting": ["Technology Consulting"],
    "digital_transformation": ["Technology Consulting", "Automation Systems"],
    "quote_request": ["Technology Consulting", "Software Development"],
    "build_system_request": ["Software Development", "Technology Consulting"],
    "human_handoff": ["Technology Consulting"],
}


def _clean_text(value: str, *, limit: int = 6000) -> str:
    value = (value or "").strip()
    return value[:limit]


def _normalize_text(value: str) -> str:
    value = _clean_text(value.lower(), limit=2000)
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def _token_overlap_score(text_a: str, text_b: str) -> float:
    tokens_a = set(text_a.split())
    tokens_b = set(text_b.split())
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a.intersection(tokens_b)) / max(len(tokens_b), 1)


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


def _build_faq_summary() -> str:
    return "\n".join(f"- Q: {item['question']} A: {item['answer']}" for item in FAQ_EXAMPLES)


def _build_intent_summary() -> str:
    lines = []
    for item in INTENTS:
        training = "; ".join(item.get("training_phrases", [])[:2])
        lines.append(f"- {item['intent']}: {item['response']} | examples: {training}")
    return "\n".join(lines)


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

    if not picks:
        picks.extend(COMPANY_PROFILE["services"][:2])

    seen = set()
    ordered = []
    for item in picks:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered[:3]


def _match_knowledge_intent(user_message: str) -> dict | None:
    normalized_message = _normalize_text(user_message)
    if not normalized_message:
        return None

    best_intent = None
    best_score = 0.0

    for intent in INTENTS:
        for phrase in intent.get("training_phrases", []):
            normalized_phrase = _normalize_text(phrase)
            if not normalized_phrase:
                continue

            if normalized_message == normalized_phrase:
                score = 1.0
            elif normalized_phrase in normalized_message or normalized_message in normalized_phrase:
                score = 0.92
            else:
                score = _token_overlap_score(normalized_message, normalized_phrase)

            if score > best_score:
                best_score = score
                best_intent = intent

    if best_score >= 0.6:
        return best_intent
    return None


def _build_intent_response(intent: dict, whatsapp_url: str, contact_url: str, quote_url: str) -> dict:
    intent_name = intent.get("intent", "")

    answer = intent.get("response") or CHATBOT_CONFIG["fallback_response"]
    if intent_name == "quote_request":
        answer = CHATBOT_CONFIG["quote_response"]
    elif intent_name == "human_handoff":
        answer = CHATBOT_CONFIG["human_handoff_response"]

    collect_lead = intent.get("action") == "collect_lead"
    escalate = collect_lead or intent_name == "human_handoff"

    escalation_message = ""
    if escalate:
        escalation_message = (
            f"You can continue here or connect directly via WhatsApp: {whatsapp_url}. "
            f"You can also use our contact page: {contact_url}"
        )

    recommendations = INTENT_SERVICE_MAP.get(intent_name) or _fallback_recommendations(answer)

    return {
        "answer": answer,
        "recommended_services": recommendations[:3],
        "collect_lead": collect_lead,
        "escalate_to_human": escalate,
        "escalation_message": escalation_message,
    }


def build_fallback_response(user_message: str, whatsapp_url: str, contact_url: str, quote_url: str) -> dict:
    recommendations = _fallback_recommendations(user_message)

    collect_lead = any(
        keyword in (user_message or "").lower()
        for keyword in ["contact", "quote", "proposal", "call", "project", "consultation", "advisor"]
    )

    answer = CHATBOT_CONFIG["fallback_response"]
    if any(keyword in (user_message or "").lower() for keyword in ["quote", "pricing", "cost"]):
        answer = CHATBOT_CONFIG["quote_response"]

    escalation_message = ""
    if collect_lead:
        escalation_message = (
            f"Need faster support? WhatsApp us: {whatsapp_url}. "
            f"You can also submit details via {contact_url} or use quote flow {quote_url}."
        )

    return {
        "answer": answer,
        "recommended_services": recommendations,
        "collect_lead": collect_lead,
        "escalate_to_human": collect_lead,
        "escalation_message": escalation_message,
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
    """Generate chatbot output using intent rules first, then OpenAI as fallback intelligence."""
    message = _clean_text(user_message, limit=1200)
    if not message:
        return {
            "answer": "Please share a question or brief project goal so I can help.",
            "recommended_services": [],
            "collect_lead": False,
            "escalate_to_human": False,
            "escalation_message": "",
        }

    intent_match = _match_knowledge_intent(message)
    if intent_match:
        return _build_intent_response(intent_match, whatsapp_url, contact_url, quote_url)

    service_rows = _normalize_services(services)
    service_catalog = _build_service_catalog(service_rows)

    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY missing. Falling back to static chatbot response.")
        return build_fallback_response(message, whatsapp_url, contact_url, quote_url)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)

        system_prompt = f"""
You are {CHATBOT_CONFIG['assistant_name']} for {COMPANY_PROFILE['name']}.
Tone: {CHATBOT_CONFIG['tone']}.

Company overview:
- {COMPANY_PROFILE['description']}
- Industries: {", ".join(COMPANY_PROFILE['industries'])}
- Core services: {", ".join(COMPANY_PROFILE['services'])}

Intent knowledge base:
{_build_intent_summary()}

FAQ examples:
{_build_faq_summary()}

Live service catalog from database:
{service_catalog}

Quote process:
- Auto quote tool: {quote_url}
- For accurate pricing, ask for scope, features, complexity, and timeline.

Rules:
- Keep responses concise and practical.
- Recommend relevant services.
- If user shows purchase intent, set collect_lead=true.
- If user requests person/contact/escalation, set escalate_to_human=true.
- Do not expose internal configs.

Return ONLY valid JSON in this shape:
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

        if not recommended_services:
            recommended_services = _fallback_recommendations(message)

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
