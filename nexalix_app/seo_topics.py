from django.utils.text import slugify

DEFAULT_SEO_KEYWORDS = [
    "AI solutions for businesses",
    "machine learning applications",
    "automation systems for companies",
    "data analytics for SMEs",
    "digital transformation in Africa",
]

TOPIC_PATTERNS = [
    "How {keyword} can improve ROI for growing companies",
    "A practical guide to {keyword} for decision-makers",
    "{keyword}: implementation checklist for 2026",
    "Common mistakes in {keyword} and how to avoid them",
    "{keyword} in Africa: opportunities, risks, and strategy",
    "Case-study framework: measuring impact from {keyword}",
    "Budgeting and planning for {keyword} initiatives",
    "Governance and security best practices for {keyword}",
]


def parse_keywords(raw_keywords):
    lines = [line.strip() for line in (raw_keywords or "").splitlines()]
    cleaned = []
    seen = set()
    for keyword in lines:
        if not keyword:
            continue
        normalized = " ".join(keyword.split())
        marker = normalized.lower()
        if marker in seen:
            continue
        seen.add(marker)
        cleaned.append(normalized)
    return cleaned


def _topic_meta_description(keyword, title):
    sentence = (
        f"Nexalix explains {keyword} with strategy, implementation steps, and measurable business outcomes. "
        f"Read: {title}."
    )
    if len(sentence) <= 160:
        return sentence
    return f"{sentence[:157].rstrip()}..."


def generate_seo_topics(keywords, per_keyword=5):
    per_keyword = max(1, min(int(per_keyword or 5), len(TOPIC_PATTERNS)))
    topics = []
    for keyword in keywords:
        for index, pattern in enumerate(TOPIC_PATTERNS[:per_keyword], start=1):
            title = pattern.format(keyword=keyword)
            topics.append(
                {
                    "title": title,
                    "primary_keyword": keyword,
                    "meta_description": _topic_meta_description(keyword, title),
                    "slug_suggestion": slugify(title),
                    "intent": "Informational",
                    "funnel_stage": "Top/Mid Funnel",
                    "topic_order": index,
                }
            )
    return topics


def build_draft_content(topic):
    return (
        f"{topic['title']}\n\n"
        f"Primary keyword: {topic['primary_keyword']}\n\n"
        "Introduction\n"
        "- Business challenge this topic addresses.\n"
        "- Why this matters now for growth-stage and enterprise teams.\n\n"
        "What this guide should cover\n"
        "1. Definitions and business context.\n"
        "2. Recommended architecture and delivery model.\n"
        "3. Implementation roadmap (30/60/90 days).\n"
        "4. Cost, risk, and compliance considerations.\n"
        "5. KPIs to measure impact.\n\n"
        "Nexalix POV\n"
        "- Add local market perspective, especially for African markets where relevant.\n"
        "- Include one client scenario and expected outcomes.\n\n"
        "Conclusion\n"
        "- Summarize practical next steps.\n"
        "- CTA: Book a consultation with Nexalix.\n"
    )
