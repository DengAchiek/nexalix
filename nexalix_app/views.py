from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.core.cache import cache
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils.text import slugify
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.urls import reverse
from urllib.parse import urlencode
from datetime import timedelta, date
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from io import BytesIO
import logging
import csv
import json
import math
import re
from .cache_utils import (
    HOME_CONTEXT_CACHE_KEY,
    get_dashboard_aggregate_cache_key,
)
from .chatbot import generate_chatbot_response
from .seo_topics import (
    DEFAULT_SEO_KEYWORDS,
    build_draft_content,
    generate_seo_topics,
    parse_keywords,
)
from .models import (
    HeroSection, Service, Testimonial, AboutSection, ProcessStep,
    Industry, TechnologyCategory, CaseStudy, NewsletterSignup,
    Statistic, BlogPost, Partner, Award, ContactCTA,
    ServiceFeature, ServiceTechnology, PricingPlan, ContactMessage,
    QuoteAddon, QuoteRequest, DashboardSavedFilter, ChatbotLead
)
# If you have these models, import them:
# from .models import AboutPage, CompanyValue, ContactInfo, ContactMessage

COMPLEXITY_MULTIPLIERS = {
    "starter": Decimal("1.00"),
    "growth": Decimal("1.25"),
    "advanced": Decimal("1.60"),
    "enterprise": Decimal("2.10"),
}

COMPLEXITY_DURATION = {
    "starter": Decimal("0.90"),
    "growth": Decimal("1.00"),
    "advanced": Decimal("1.15"),
    "enterprise": Decimal("1.35"),
}

TIMELINE_MULTIPLIERS = {
    "standard": Decimal("1.00"),
    "accelerated": Decimal("1.18"),
    "urgent": Decimal("1.35"),
}

TIMELINE_DURATION = {
    "standard": Decimal("1.00"),
    "accelerated": Decimal("0.75"),
    "urgent": Decimal("0.55"),
}

SUPPORT_MULTIPLIERS = {
    "none": Decimal("0.00"),
    "standard": Decimal("0.08"),
    "premium": Decimal("0.15"),
}

HOME_CONTEXT_CACHE_TTL = int(getattr(settings, "HOME_CACHE_TIMEOUT", 300))
DASHBOARD_AGGREGATES_CACHE_TTL = int(getattr(settings, "DASHBOARD_CACHE_TIMEOUT", 120))
CHATBOT_HISTORY_SESSION_KEY = "chatbot_history"
CHATBOT_HISTORY_MAX_ITEMS = int(getattr(settings, "CHATBOT_SESSION_HISTORY_LIMIT", 16))
DASHBOARD_CONTACT_SLA_HOURS = max(1, int(getattr(settings, "DASHBOARD_CONTACT_SLA_HOURS", 4)))
DASHBOARD_QUOTE_SLA_HOURS = max(1, int(getattr(settings, "DASHBOARD_QUOTE_SLA_HOURS", 24)))
ALERT_SPIKE_MULTIPLIER = float(getattr(settings, "DASHBOARD_ALERT_SPIKE_MULTIPLIER", 1.8))
ALERT_SPIKE_MIN_ABS_DELTA = int(getattr(settings, "DASHBOARD_ALERT_SPIKE_MIN_ABS_DELTA", 3))
EMAIL_ALERT_GRACE_MINUTES = int(getattr(settings, "DASHBOARD_EMAIL_ALERT_GRACE_MINUTES", 15))
STALE_CONTACT_HOURS = int(getattr(settings, "DASHBOARD_STALE_CONTACT_HOURS", 72))
STALE_QUOTE_HOURS = int(getattr(settings, "DASHBOARD_STALE_QUOTE_HOURS", 168))
HOME_AB_VARIANTS = ("A", "B")

logger = logging.getLogger("nexalix_app.views")


def _money(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _text_excerpt(value, limit=160):
    text = (value or "").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit - 1].rstrip()}…"


def _build_keywords(*keyword_groups):
    baseline = [
        "technology consulting",
        "software development",
        "ai solutions",
        "digital transformation",
    ]
    ordered = []
    seen = set()

    def _add(keyword):
        normalized = str(keyword or "").strip().lower()
        if not normalized or normalized in seen:
            return
        seen.add(normalized)
        ordered.append(normalized)

    for item in baseline:
        _add(item)

    for group in keyword_groups:
        if isinstance(group, (list, tuple, set)):
            for item in group:
                _add(item)
        else:
            _add(group)

    return ", ".join(ordered[:18])


def _resolve_home_ab_variant(request, default_headline, default_subtitle):
    forced_variant = (request.GET.get("ab") or "").strip().upper()
    if forced_variant in HOME_AB_VARIANTS:
        request.session["home_ab_variant"] = forced_variant
        variant = forced_variant
    else:
        variant = (request.session.get("home_ab_variant") or "").strip().upper()
        if variant not in HOME_AB_VARIANTS:
            session_key = _ensure_session_key(request)
            bucket = sum(ord(ch) for ch in session_key) % 2 if session_key else 0
            variant = "A" if bucket == 0 else "B"
            request.session["home_ab_variant"] = variant
            request.session.modified = True

    if variant == "B":
        return {
            "test_name": "home_hero_primary",
            "variant": "B",
            "headline": "Build Resilient Digital Systems That Scale With Your Business",
            "subtitle": "From product strategy to implementation, we help teams ship faster, automate operations, and grow with confidence.",
            "primary_cta_text": "Book Strategy Call",
            "primary_cta_url": reverse("contact"),
        }

    return {
        "test_name": "home_hero_primary",
        "variant": "A",
        "headline": default_headline,
        "subtitle": default_subtitle,
        "primary_cta_text": "Explore Services",
        "primary_cta_url": reverse("services"),
    }


def _absolute_url(request, path_or_url):
    if not path_or_url:
        return ""
    if str(path_or_url).startswith(("http://", "https://")):
        return str(path_or_url)
    return request.build_absolute_uri(path_or_url)


def _format_remaining_time(delta):
    total_seconds = int(delta.total_seconds())
    if total_seconds <= 0:
        return "Overdue"
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    if hours <= 0:
        return f"{minutes}m left"
    if minutes == 0:
        return f"{hours}h left"
    return f"{hours}h {minutes}m left"


def _sla_bucket_for_seconds(remaining_seconds):
    if remaining_seconds <= 0:
        return "overdue"
    if remaining_seconds <= 3600:
        return "within_1h"
    if remaining_seconds <= 4 * 3600:
        return "within_4h"
    if remaining_seconds <= 24 * 3600:
        return "within_24h"
    return "on_track"


def _organization_schema(request):
    logo_url = _absolute_url(request, "/static/images/logo1.png")
    site_url = _absolute_url(request, "/")
    return {
        "@context": "https://schema.org",
        "@type": "Organization",
        "@id": f"{site_url}#organization",
        "name": "Nexalix Technologies",
        "url": site_url,
        "logo": logo_url,
        "email": "info@nexalixtech.com",
        "telephone": "+254768774232",
        "address": {
            "@type": "PostalAddress",
            "addressCountry": "KE",
        },
    }


def _service_schema(request, service, position=None):
    service_slug = service.slug or slugify(service.title)
    if service_slug:
        service_url = _absolute_url(request, reverse("service_detail", args=[service_slug]))
    else:
        service_url = _absolute_url(request, reverse("services"))
    data = {
        "@type": "Service",
        "name": service.title,
        "url": service_url,
        "description": _text_excerpt(service.meta_description or service.short_description, limit=260),
        "provider": {
            "@type": "Organization",
            "name": "Nexalix Technologies",
            "url": _absolute_url(request, "/"),
        },
    }
    if service.featured_image:
        data["image"] = _absolute_url(request, service.featured_image.url)
    if position is not None:
        return {"@type": "ListItem", "position": position, "url": service_url, "item": data}
    return data


def _case_study_schema(request, case_study, position=None):
    case_url = _absolute_url(request, reverse("case_study_detail", args=[slugify(case_study.title)]))
    data = {
        "@type": "CreativeWork",
        "name": case_study.title,
        "url": case_url,
        "description": _text_excerpt(case_study.description, limit=260),
    }
    if case_study.image:
        data["image"] = _absolute_url(request, case_study.image.url)
    if case_study.tags:
        data["keywords"] = [tag.strip() for tag in case_study.tags.split(",") if tag.strip()]
    if position is not None:
        return {"@type": "ListItem", "position": position, "url": case_url, "item": data}
    return data


def _seo_context(
    request,
    *,
    title,
    description,
    keywords="technology consulting, AI solutions, software development, cloud services, cybersecurity",
    og_type="website",
    image_url="",
    schemas=None,
):
    canonical_url = request.build_absolute_uri(request.path)
    resolved_image = _absolute_url(request, image_url or "/static/images/logo1.png")

    schema_payloads = [
        _organization_schema(request),
        {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": title,
            "url": canonical_url,
            "description": _text_excerpt(description, limit=260),
        },
    ]
    if schemas:
        schema_payloads.extend(schemas)

    return {
        "meta_title": title,
        "meta_description": _text_excerpt(description, limit=160),
        "meta_keywords": keywords,
        "canonical_url": canonical_url,
        "og_title": title,
        "og_description": _text_excerpt(description, limit=200),
        "og_type": og_type,
        "og_url": canonical_url,
        "og_image": resolved_image,
        "twitter_card": "summary_large_image",
        "structured_data_json": [json.dumps(schema, ensure_ascii=False) for schema in schema_payloads],
    }


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


ROLE_LABELS = {
    "all": "All Views",
    "sales": "Sales View",
    "ops": "Ops View",
}

INDUSTRY_KEYWORD_MAP = (
    ("health", "Healthcare"),
    ("hospital", "Healthcare"),
    ("clinic", "Healthcare"),
    ("edu", "Education"),
    ("school", "Education"),
    ("university", "Education"),
    ("bank", "Finance"),
    ("fin", "Finance"),
    ("payment", "Finance"),
    ("shop", "Retail"),
    ("retail", "Retail"),
    ("store", "Retail"),
    ("logistic", "Logistics"),
    ("supply", "Logistics"),
    ("transport", "Logistics"),
    ("startup", "Startups"),
    ("saas", "Startups"),
)


def _safe_parse_iso_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _allowed_role_views(user):
    if not user.is_authenticated:
        return ["all"]
    if user.is_superuser:
        return ["all", "sales", "ops"]

    group_names = {name.lower() for name in user.groups.values_list("name", flat=True)}
    allowed = []
    if "sales" in group_names:
        allowed.append("sales")
    if "ops" in group_names or "operations" in group_names:
        allowed.append("ops")
    if not allowed:
        return ["all"]
    return ["all", *allowed]


def _dashboard_query_string(period_days, activity_filter, search_query, role_view, day_value=""):
    params = {"period": str(period_days)}
    if search_query:
        params["q"] = search_query
    if activity_filter and activity_filter != "all":
        params["activity"] = activity_filter
    if role_view and role_view != "all":
        params["role"] = role_view
    if day_value:
        params["day"] = day_value
    return urlencode(params)


def _safe_ratio_percent(numerator, denominator):
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def _normalize_service_label(value):
    label = (value or "").strip()
    if not label:
        return "Unspecified"
    return label[:80]


def _infer_industry_label(text, known_industries):
    raw = (text or "").strip().lower()
    if not raw:
        return "Unspecified"

    for industry in known_industries:
        if industry and industry.lower() in raw:
            return industry

    for keyword, fallback_label in INDUSTRY_KEYWORD_MAP:
        if keyword in raw:
            return fallback_label

    return "Unspecified"


def _build_funnel_rows(contact_counts, quote_counts, won_counts, lost_counts, limit=8):
    labels = set(contact_counts.keys()) | set(quote_counts.keys()) | set(won_counts.keys()) | set(lost_counts.keys())
    rows = []
    for label in labels:
        contacts = int(contact_counts.get(label, 0))
        quotes = int(quote_counts.get(label, 0))
        won = int(won_counts.get(label, 0))
        lost = int(lost_counts.get(label, 0))
        rows.append({
            "label": label,
            "contacts": contacts,
            "quotes": quotes,
            "won": won,
            "lost": lost,
            "drop_contact_to_quote": max(contacts - quotes, 0),
            "drop_quote_to_won": max(quotes - won, 0),
            "contact_to_quote_rate": _safe_ratio_percent(quotes, contacts),
            "quote_to_won_rate": _safe_ratio_percent(won, quotes),
        })

    rows.sort(key=lambda item: (item["quotes"], item["contacts"]), reverse=True)
    return rows[:limit]


def _build_funnel_analytics(contacts_queryset, quotes_queryset):
    known_industries = list(
        Industry.objects.filter(is_active=True)
        .order_by("order", "name")
        .values_list("name", flat=True)
    )

    contact_service_counts = defaultdict(int)
    quote_service_counts = defaultdict(int)
    won_service_counts = defaultdict(int)
    lost_service_counts = defaultdict(int)

    contact_industry_counts = defaultdict(int)
    quote_industry_counts = defaultdict(int)
    won_industry_counts = defaultdict(int)
    lost_industry_counts = defaultdict(int)

    for message in contacts_queryset.only("service", "message"):
        service_label = _normalize_service_label(message.service)
        industry_label = _infer_industry_label(f"{message.service} {message.message}", known_industries)
        contact_service_counts[service_label] += 1
        contact_industry_counts[industry_label] += 1

    for quote in quotes_queryset.select_related("service").only("status", "company", "project_summary", "service__title"):
        service_label = _normalize_service_label(quote.service.title if quote.service else "")
        industry_label = _infer_industry_label(
            f"{quote.company} {quote.project_summary} {quote.service.title if quote.service else ''}",
            known_industries,
        )
        quote_service_counts[service_label] += 1
        quote_industry_counts[industry_label] += 1
        if quote.status == "won":
            won_service_counts[service_label] += 1
            won_industry_counts[industry_label] += 1
        elif quote.status == "lost":
            lost_service_counts[service_label] += 1
            lost_industry_counts[industry_label] += 1

    contacts_total = int(sum(contact_service_counts.values()))
    quotes_total = int(sum(quote_service_counts.values()))
    won_total = int(sum(won_service_counts.values()))
    lost_total = int(sum(lost_service_counts.values()))

    return {
        "overall": {
            "contacts": contacts_total,
            "quotes": quotes_total,
            "won": won_total,
            "lost": lost_total,
            "drop_contact_to_quote": max(contacts_total - quotes_total, 0),
            "drop_quote_to_won": max(quotes_total - won_total, 0),
            "contact_to_quote_rate": _safe_ratio_percent(quotes_total, contacts_total),
            "quote_to_won_rate": _safe_ratio_percent(won_total, quotes_total),
        },
        "service_rows": _build_funnel_rows(
            contact_service_counts,
            quote_service_counts,
            won_service_counts,
            lost_service_counts,
            limit=8,
        ),
        "industry_rows": _build_funnel_rows(
            contact_industry_counts,
            quote_industry_counts,
            won_industry_counts,
            lost_industry_counts,
            limit=8,
        ),
    }


def _build_sla_snapshot(filtered_contacts, filtered_quotes, now):
    summary = {
        "overdue": 0,
        "within_1h": 0,
        "within_4h": 0,
        "within_24h": 0,
        "on_track": 0,
    }
    queue = []

    def _append(kind, created_at, title, subtitle, status_label, admin_url, sla_hours):
        due_at = created_at + timedelta(hours=sla_hours)
        remaining = due_at - now
        remaining_seconds = int(remaining.total_seconds())
        bucket = _sla_bucket_for_seconds(remaining_seconds)
        summary[bucket] += 1
        queue.append({
            "kind": kind,
            "title": title,
            "subtitle": subtitle,
            "status": status_label,
            "admin_url": admin_url,
            "due_at": due_at,
            "remaining_label": _format_remaining_time(remaining),
            "remaining_seconds": remaining_seconds,
            "bucket": bucket,
        })

    pending_contacts = filtered_contacts.filter(is_read=False).order_by("submitted_at")
    pending_quotes = filtered_quotes.filter(status__in=["new", "reviewed", "sent"]).select_related("service").order_by("created_at")

    for message in pending_contacts.iterator():
        _append(
            kind="contact",
            created_at=message.submitted_at,
            title=message.full_name,
            subtitle=message.service or "General inquiry",
            status_label="Unread",
            admin_url=reverse("admin:nexalix_app_contactmessage_change", args=[message.id]),
            sla_hours=DASHBOARD_CONTACT_SLA_HOURS,
        )

    for quote in pending_quotes.iterator():
        _append(
            kind="quote",
            created_at=quote.created_at,
            title=quote.quote_reference,
            subtitle=quote.service.title if quote.service else "Service not selected",
            status_label=quote.get_status_display(),
            admin_url=reverse("admin:nexalix_app_quoterequest_change", args=[quote.id]),
            sla_hours=DASHBOARD_QUOTE_SLA_HOURS,
        )

    queue.sort(key=lambda item: item["remaining_seconds"])
    for item in queue:
        item["due_at_label"] = timezone.localtime(item["due_at"]).strftime("%b %d, %H:%M")
    queue = queue[:12]
    summary["pending_total"] = (
        summary["overdue"]
        + summary["within_1h"]
        + summary["within_4h"]
        + summary["within_24h"]
        + summary["on_track"]
    )
    return summary, queue


def _build_client_activities(filtered_contacts, filtered_quotes, role_view, limit=60):
    activities = []
    for message in filtered_contacts.order_by("-submitted_at")[:50]:
        activities.append({
            "type": "contact",
            "title": f"Contact from {message.full_name}",
            "subtitle": message.service or "General inquiry",
            "detail": message.email,
            "timestamp": message.submitted_at,
            "status": "Unread" if not message.is_read else "Read",
            "admin_url": reverse("admin:nexalix_app_contactmessage_change", args=[message.id]),
            "search_text": f"{message.full_name} {message.email} {message.service or ''} {message.message}".lower(),
        })

    for quote in filtered_quotes.order_by("-created_at")[:50]:
        activities.append({
            "type": "quote",
            "title": f"Quote request {quote.quote_reference}",
            "subtitle": quote.service.title if quote.service else "Service not selected",
            "detail": quote.email,
            "timestamp": quote.created_at,
            "status": quote.get_status_display(),
            "admin_url": reverse("admin:nexalix_app_quoterequest_change", args=[quote.id]),
            "search_text": f"{quote.quote_reference} {quote.full_name} {quote.email} {quote.company or ''} {quote.project_summary}".lower(),
        })

    if role_view == "ops":
        activities = [
            item for item in activities
            if item["type"] == "contact" or item["status"] in {"New", "Reviewed", "Quote Sent"}
        ]

    activities.sort(key=lambda item: item["timestamp"], reverse=True)
    return activities[:limit]


def _is_likely_valid_email(value):
    email = (value or "").strip()
    if not email or "@" not in email or "." not in email:
        return False
    if ".." in email or email.startswith("@") or email.endswith("@"):
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def _is_likely_valid_phone(value):
    phone = (value or "").strip()
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    if len(digits) < 7 or len(digits) > 15:
        return False
    return bool(re.match(r"^[0-9+\-\s()]+$", phone))


def _build_alert_center(now, contacts_queryset, quotes_queryset, sla_summary):
    alerts = []
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "info": 1}

    lookback_24h = now - timedelta(hours=24)
    previous_window_start = now - timedelta(days=8)
    previous_window_end = lookback_24h

    contacts_last_24h = contacts_queryset.filter(submitted_at__gte=lookback_24h).count()
    contacts_prev_count = contacts_queryset.filter(
        submitted_at__gte=previous_window_start,
        submitted_at__lt=previous_window_end,
    ).count()
    contacts_prev_daily_avg = contacts_prev_count / 7 if contacts_prev_count else 0

    quotes_last_24h = quotes_queryset.filter(created_at__gte=lookback_24h).count()
    quotes_prev_count = quotes_queryset.filter(
        created_at__gte=previous_window_start,
        created_at__lt=previous_window_end,
    ).count()
    quotes_prev_daily_avg = quotes_prev_count / 7 if quotes_prev_count else 0

    if contacts_prev_daily_avg > 0 and (
        contacts_last_24h >= contacts_prev_daily_avg * ALERT_SPIKE_MULTIPLIER
        and contacts_last_24h - contacts_prev_daily_avg >= ALERT_SPIKE_MIN_ABS_DELTA
    ):
        alerts.append({
            "code": "contact_spike",
            "severity": "high",
            "title": "Contact volume spike",
            "message": f"{contacts_last_24h} contacts in 24h vs {contacts_prev_daily_avg:.1f} avg/day baseline.",
            "action_url": reverse("admin:nexalix_app_contactmessage_changelist"),
        })

    if quotes_prev_daily_avg > 0 and (
        quotes_last_24h >= quotes_prev_daily_avg * ALERT_SPIKE_MULTIPLIER
        and quotes_last_24h - quotes_prev_daily_avg >= ALERT_SPIKE_MIN_ABS_DELTA
    ):
        alerts.append({
            "code": "quote_spike",
            "severity": "high",
            "title": "Quote request spike",
            "message": f"{quotes_last_24h} quotes in 24h vs {quotes_prev_daily_avg:.1f} avg/day baseline.",
            "action_url": reverse("admin:nexalix_app_quoterequest_changelist"),
        })

    overdue_count = int(sla_summary.get("overdue", 0))
    if overdue_count > 0:
        alerts.append({
            "code": "overdue_leads",
            "severity": "critical",
            "title": "Overdue lead responses",
            "message": f"{overdue_count} leads are overdue based on SLA targets.",
            "action_url": reverse("activity_dashboard"),
        })

    grace_cutoff = now - timedelta(minutes=EMAIL_ALERT_GRACE_MINUTES)
    email_failure_count = ContactMessage.objects.filter(
        submitted_at__lte=grace_cutoff
    ).filter(
        Q(admin_notified=False) | Q(user_confirmation_sent=False)
    ).count()
    if email_failure_count > 0:
        alerts.append({
            "code": "email_failures",
            "severity": "medium",
            "title": "Email notification failures",
            "message": f"{email_failure_count} contact messages appear unsent after {EMAIL_ALERT_GRACE_MINUTES} minutes.",
            "action_url": reverse("admin:nexalix_app_contactmessage_changelist"),
        })

    escalations_7d = ChatbotLead.objects.filter(
        created_at__gte=now - timedelta(days=7),
        is_escalated=True,
    ).count()
    if escalations_7d > 0:
        alerts.append({
            "code": "chatbot_escalations",
            "severity": "info" if escalations_7d < 5 else "medium",
            "title": "Chatbot escalations",
            "message": f"{escalations_7d} chatbot conversations escalated to human channels in the last 7 days.",
            "action_url": reverse("admin:nexalix_app_chatbotlead_changelist"),
        })

    alerts.sort(key=lambda item: severity_rank.get(item["severity"], 0), reverse=True)
    summary = {
        "critical": sum(1 for item in alerts if item["severity"] == "critical"),
        "high": sum(1 for item in alerts if item["severity"] == "high"),
        "medium": sum(1 for item in alerts if item["severity"] == "medium"),
        "info": sum(1 for item in alerts if item["severity"] == "info"),
        "total": len(alerts),
    }
    return summary, alerts[:12]


def _build_data_quality_checks(now, contacts_queryset, quotes_queryset):
    issues = []
    severity_rank = {"critical": 4, "high": 3, "medium": 2, "low": 1}

    contact_email_dups = list(
        contacts_queryset.exclude(email__isnull=True).exclude(email__exact="")
        .values("email")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .order_by("-total")[:6]
    )
    quote_email_dups = list(
        quotes_queryset.exclude(email__isnull=True).exclude(email__exact="")
        .values("email")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
        .order_by("-total")[:6]
    )

    for dup in contact_email_dups:
        email = dup["email"]
        issues.append({
            "code": "duplicate_contact_email",
            "severity": "medium",
            "category": "Duplicate",
            "label": f"Contact email duplicated: {email}",
            "detail": f"{dup['total']} contact records share this email.",
            "action_url": f"{reverse('admin:nexalix_app_contactmessage_changelist')}?email__icontains={email}",
        })
    for dup in quote_email_dups:
        email = dup["email"]
        issues.append({
            "code": "duplicate_quote_email",
            "severity": "medium",
            "category": "Duplicate",
            "label": f"Quote email duplicated: {email}",
            "detail": f"{dup['total']} quote requests share this email.",
            "action_url": f"{reverse('admin:nexalix_app_quoterequest_changelist')}?email__icontains={email}",
        })

    invalid_contact_emails = []
    for item in contacts_queryset.only("id", "email", "full_name").exclude(email__isnull=True)[:200]:
        if not _is_likely_valid_email(item.email):
            invalid_contact_emails.append(item)

    invalid_quote_emails = []
    invalid_quote_phones = []
    for item in quotes_queryset.only("id", "email", "phone", "quote_reference").exclude(email__isnull=True)[:300]:
        if not _is_likely_valid_email(item.email):
            invalid_quote_emails.append(item)
        if item.phone and not _is_likely_valid_phone(item.phone):
            invalid_quote_phones.append(item)

    for item in invalid_contact_emails[:6]:
        issues.append({
            "code": "invalid_contact_email",
            "severity": "high",
            "category": "Validation",
            "label": f"Invalid contact email: {item.email}",
            "detail": f"Contact record for {item.full_name} has malformed email.",
            "action_url": reverse("admin:nexalix_app_contactmessage_change", args=[item.id]),
        })
    for item in invalid_quote_emails[:6]:
        issues.append({
            "code": "invalid_quote_email",
            "severity": "high",
            "category": "Validation",
            "label": f"Invalid quote email: {item.email}",
            "detail": f"Quote {item.quote_reference} has malformed email.",
            "action_url": reverse("admin:nexalix_app_quoterequest_change", args=[item.id]),
        })
    for item in invalid_quote_phones[:6]:
        issues.append({
            "code": "invalid_quote_phone",
            "severity": "medium",
            "category": "Validation",
            "label": f"Invalid phone on quote {item.quote_reference}",
            "detail": f"Phone value '{item.phone}' is likely invalid.",
            "action_url": reverse("admin:nexalix_app_quoterequest_change", args=[item.id]),
        })

    missing_contact_fields = contacts_queryset.filter(
        Q(full_name__isnull=True) | Q(full_name__exact="") | Q(message__isnull=True) | Q(message__exact="")
    )[:6]
    missing_quote_fields = quotes_queryset.filter(
        Q(full_name__isnull=True) | Q(full_name__exact="") | Q(email__isnull=True) | Q(email__exact="")
        | Q(project_summary__isnull=True) | Q(project_summary__exact="")
    )[:6]

    for item in missing_contact_fields:
        issues.append({
            "code": "missing_contact_fields",
            "severity": "high",
            "category": "Missing fields",
            "label": f"Contact {item.id} missing required fields",
            "detail": "Full name or message is empty.",
            "action_url": reverse("admin:nexalix_app_contactmessage_change", args=[item.id]),
        })
    for item in missing_quote_fields:
        issues.append({
            "code": "missing_quote_fields",
            "severity": "high",
            "category": "Missing fields",
            "label": f"Quote {item.quote_reference} missing required fields",
            "detail": "Name, email, or project summary is empty.",
            "action_url": reverse("admin:nexalix_app_quoterequest_change", args=[item.id]),
        })

    stale_contact_cutoff = now - timedelta(hours=STALE_CONTACT_HOURS)
    stale_quote_cutoff = now - timedelta(hours=STALE_QUOTE_HOURS)
    stale_contacts = contacts_queryset.filter(is_read=False, submitted_at__lt=stale_contact_cutoff)[:10]
    stale_quotes = quotes_queryset.filter(status__in=["new", "reviewed", "sent"], created_at__lt=stale_quote_cutoff)[:10]

    for item in stale_contacts:
        issues.append({
            "code": "stale_contact",
            "severity": "high",
            "category": "Stale records",
            "label": f"Stale unread contact: {item.full_name}",
            "detail": f"No response for more than {STALE_CONTACT_HOURS} hours.",
            "action_url": reverse("admin:nexalix_app_contactmessage_change", args=[item.id]),
        })
    for item in stale_quotes:
        issues.append({
            "code": "stale_quote",
            "severity": "high",
            "category": "Stale records",
            "label": f"Stale quote: {item.quote_reference}",
            "detail": f"Quote is still open after {STALE_QUOTE_HOURS} hours.",
            "action_url": reverse("admin:nexalix_app_quoterequest_change", args=[item.id]),
        })

    summary = {
        "duplicates": len(contact_email_dups) + len(quote_email_dups),
        "invalid_emails": len(invalid_contact_emails) + len(invalid_quote_emails),
        "invalid_phones": len(invalid_quote_phones),
        "missing_fields": len(missing_contact_fields) + len(missing_quote_fields),
        "stale_records": len(stale_contacts) + len(stale_quotes),
    }
    summary["total_issues"] = (
        summary["duplicates"]
        + summary["invalid_emails"]
        + summary["invalid_phones"]
        + summary["missing_fields"]
        + summary["stale_records"]
    )

    issues.sort(key=lambda item: severity_rank.get(item["severity"], 0), reverse=True)
    return summary, issues[:20]


def _build_weekly_exec_snapshot(now, role_view="all"):
    week_start = now - timedelta(days=7)
    contacts_queryset = ContactMessage.objects.filter(submitted_at__gte=week_start)
    quotes_queryset = QuoteRequest.objects.select_related("service").filter(created_at__gte=week_start)
    if role_view == "ops":
        contacts_queryset = contacts_queryset.filter(is_read=False)
        quotes_queryset = quotes_queryset.filter(status__in=["new", "reviewed", "sent"])
    elif role_view == "sales":
        quotes_queryset = quotes_queryset.exclude(status="lost")

    contacts_count = contacts_queryset.count()
    quotes_count = quotes_queryset.count()
    quotes_won = quotes_queryset.filter(status="won").count()
    quotes_lost = quotes_queryset.filter(status="lost").count()
    contacts_unread = contacts_queryset.filter(is_read=False).count()
    quotes_new = quotes_queryset.filter(status="new").count()

    contacts_daily_raw = contacts_queryset.annotate(day=TruncDate("submitted_at")).values("day").annotate(total=Count("id"))
    quotes_daily_raw = quotes_queryset.annotate(day=TruncDate("created_at")).values("day").annotate(total=Count("id"))
    contacts_daily = {item["day"]: item["total"] for item in contacts_daily_raw}
    quotes_daily = {item["day"]: item["total"] for item in quotes_daily_raw}

    trend_rows = []
    for i in range(7):
        day = (week_start.date() + timedelta(days=i + 1))
        trend_rows.append({
            "date": day.isoformat(),
            "contacts": int(contacts_daily.get(day, 0)),
            "quotes": int(quotes_daily.get(day, 0)),
        })

    sla_summary, _ = _build_sla_snapshot(contacts_queryset, quotes_queryset, now)
    alerts_summary, _ = _build_alert_center(now, ContactMessage.objects.all(), QuoteRequest.objects.all(), sla_summary)
    quality_summary, _ = _build_data_quality_checks(now, contacts_queryset, quotes_queryset)
    funnel = _build_funnel_analytics(contacts_queryset, quotes_queryset)

    return {
        "generated_at": timezone.localtime(now).strftime("%Y-%m-%d %H:%M:%S"),
        "window_start": week_start.date().isoformat(),
        "window_end": now.date().isoformat(),
        "role_view": role_view,
        "kpis": {
            "contacts": contacts_count,
            "quotes": quotes_count,
            "won": quotes_won,
            "lost": quotes_lost,
            "contacts_unread": contacts_unread,
            "quotes_new": quotes_new,
        },
        "conversion": {
            "contact_to_quote_rate": _safe_ratio_percent(quotes_count, contacts_count),
            "quote_to_won_rate": _safe_ratio_percent(quotes_won, quotes_count),
            "drop_contact_to_quote": max(contacts_count - quotes_count, 0),
            "drop_quote_to_won": max(quotes_count - quotes_won, 0),
        },
        "trend_rows": trend_rows,
        "sla_summary": sla_summary,
        "alerts_summary": alerts_summary,
        "quality_summary": quality_summary,
        "top_services": funnel["service_rows"][:5],
        "top_industries": funnel["industry_rows"][:5],
    }


def _safe_funnel_analytics(contacts_queryset, quotes_queryset):
    try:
        return _build_funnel_analytics(contacts_queryset, quotes_queryset)
    except Exception as exc:  # pragma: no cover - defensive in production
        logger.exception("Funnel analytics computation failed: %s", exc)
        return {
            "overall": {
                "contacts": 0,
                "quotes": 0,
                "won": 0,
                "lost": 0,
                "drop_contact_to_quote": 0,
                "drop_quote_to_won": 0,
                "contact_to_quote_rate": 0.0,
                "quote_to_won_rate": 0.0,
            },
            "service_rows": [],
            "industry_rows": [],
        }


def _safe_alert_center(now, contacts_queryset, quotes_queryset, sla_summary):
    try:
        return _build_alert_center(now, contacts_queryset, quotes_queryset, sla_summary)
    except Exception as exc:  # pragma: no cover - defensive in production
        logger.exception("Alert center computation failed: %s", exc)
        return (
            {"critical": 0, "high": 0, "medium": 0, "info": 0, "total": 0},
            [],
        )


def _safe_data_quality(now, contacts_queryset, quotes_queryset):
    try:
        return _build_data_quality_checks(now, contacts_queryset, quotes_queryset)
    except Exception as exc:  # pragma: no cover - defensive in production
        logger.exception("Data quality computation failed: %s", exc)
        return (
            {
                "duplicates": 0,
                "invalid_emails": 0,
                "invalid_phones": 0,
                "missing_fields": 0,
                "stale_records": 0,
                "total_issues": 0,
            },
            [],
        )


def _weekly_report_csv_response(snapshot):
    response = HttpResponse(content_type="text/csv")
    ts = timezone.now().strftime("%Y%m%d_%H%M")
    response["Content-Disposition"] = f'attachment; filename="nexalix_weekly_executive_{ts}.csv"'
    writer = csv.writer(response)

    writer.writerow(["Nexalix Executive Weekly Report"])
    writer.writerow(["Generated At", snapshot["generated_at"]])
    writer.writerow(["Window", f"{snapshot['window_start']} to {snapshot['window_end']}"])
    writer.writerow(["Role View", snapshot["role_view"]])
    writer.writerow([])

    writer.writerow(["KPI", "Value"])
    for key, value in snapshot["kpis"].items():
        writer.writerow([key, value])
    writer.writerow([])

    writer.writerow(["Conversion Metric", "Value"])
    for key, value in snapshot["conversion"].items():
        writer.writerow([key, value])
    writer.writerow([])

    writer.writerow(["SLA", "Value"])
    for key, value in snapshot["sla_summary"].items():
        writer.writerow([key, value])
    writer.writerow([])

    writer.writerow(["Alert Summary", "Value"])
    for key, value in snapshot["alerts_summary"].items():
        writer.writerow([key, value])
    writer.writerow([])

    writer.writerow(["Data Quality Summary", "Value"])
    for key, value in snapshot["quality_summary"].items():
        writer.writerow([key, value])
    writer.writerow([])

    writer.writerow(["Daily Trend", "Contacts", "Quotes"])
    for row in snapshot["trend_rows"]:
        writer.writerow([row["date"], row["contacts"], row["quotes"]])
    writer.writerow([])

    writer.writerow(["Top Services", "Contacts", "Quotes", "Won", "Lost", "C2Q%", "Q2W%"])
    for row in snapshot["top_services"]:
        writer.writerow([
            row["label"],
            row["contacts"],
            row["quotes"],
            row["won"],
            row["lost"],
            row["contact_to_quote_rate"],
            row["quote_to_won_rate"],
        ])
    writer.writerow([])

    writer.writerow(["Top Industries", "Contacts", "Quotes", "Won", "Lost", "C2Q%", "Q2W%"])
    for row in snapshot["top_industries"]:
        writer.writerow([
            row["label"],
            row["contacts"],
            row["quotes"],
            row["won"],
            row["lost"],
            row["contact_to_quote_rate"],
            row["quote_to_won_rate"],
        ])
    return response


def _weekly_report_pdf_response(snapshot):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 40

    def write_line(text, font="Helvetica", size=10, gap=14):
        nonlocal y
        if y < 50:
            pdf.showPage()
            y = height - 40
        pdf.setFont(font, size)
        pdf.drawString(40, y, str(text)[:120])
        y -= gap

    write_line("Nexalix Executive Weekly Report", font="Helvetica-Bold", size=15, gap=18)
    write_line(f"Generated At: {snapshot['generated_at']}")
    write_line(f"Window: {snapshot['window_start']} to {snapshot['window_end']}")
    write_line(f"Role View: {snapshot['role_view']}")
    y -= 6

    write_line("KPIs", font="Helvetica-Bold", size=12, gap=16)
    for key, value in snapshot["kpis"].items():
        write_line(f"- {key}: {value}")

    y -= 4
    write_line("Conversion", font="Helvetica-Bold", size=12, gap=16)
    for key, value in snapshot["conversion"].items():
        write_line(f"- {key}: {value}")

    y -= 4
    write_line("SLA", font="Helvetica-Bold", size=12, gap=16)
    for key, value in snapshot["sla_summary"].items():
        write_line(f"- {key}: {value}")

    y -= 4
    write_line("Alert Summary", font="Helvetica-Bold", size=12, gap=16)
    for key, value in snapshot["alerts_summary"].items():
        write_line(f"- {key}: {value}")

    y -= 4
    write_line("Data Quality Summary", font="Helvetica-Bold", size=12, gap=16)
    for key, value in snapshot["quality_summary"].items():
        write_line(f"- {key}: {value}")

    y -= 4
    write_line("Daily Trend (Contacts / Quotes)", font="Helvetica-Bold", size=12, gap=16)
    for row in snapshot["trend_rows"]:
        write_line(f"- {row['date']}: {row['contacts']} / {row['quotes']}")

    pdf.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    ts = timezone.now().strftime("%Y%m%d_%H%M")
    response["Content-Disposition"] = f'attachment; filename="nexalix_weekly_executive_{ts}.pdf"'
    return response


def calculate_quote_estimate(service, complexity, timeline, support_plan, addons):
    base_price = Decimal(service.quote_base_price or 0)
    complexity_multiplier = COMPLEXITY_MULTIPLIERS.get(complexity, Decimal("1.00"))
    timeline_multiplier = TIMELINE_MULTIPLIERS.get(timeline, Decimal("1.00"))
    support_multiplier = SUPPORT_MULTIPLIERS.get(support_plan, Decimal("0.00"))

    subtotal = base_price * complexity_multiplier * timeline_multiplier
    addons_total = sum((Decimal(addon.price) for addon in addons), Decimal("0.00"))
    support_total = subtotal * support_multiplier
    total = subtotal + addons_total + support_total
    min_estimate = total * Decimal("0.90")
    max_estimate = total * Decimal("1.10")

    weeks_base = Decimal(service.quote_delivery_weeks or 8)
    estimated_weeks = math.ceil(
        float(
            weeks_base
            * COMPLEXITY_DURATION.get(complexity, Decimal("1.00"))
            * TIMELINE_DURATION.get(timeline, Decimal("1.00"))
        )
    )

    return {
        "subtotal": _money(subtotal),
        "addons_total": _money(addons_total),
        "support_total": _money(support_total),
        "total": _money(total),
        "min_estimate": _money(min_estimate),
        "max_estimate": _money(max_estimate),
        "estimated_weeks": max(2, estimated_weeks),
    }

def home(request):
    """Home page view"""
    context = cache.get(HOME_CONTEXT_CACHE_KEY)
    if context is None:
        context = {
            "hero": HeroSection.objects.filter(is_active=True).first(),
            "services": list(Service.objects.filter(is_featured=True).order_by("order")[:3]),
            "testimonials": list(Testimonial.objects.filter(is_active=True).order_by("-created_at")[:2]),
            "about": AboutSection.objects.filter(is_active=True).first(),
            "process_steps": list(ProcessStep.objects.all().order_by("order")),
            "industries": list(Industry.objects.filter(is_active=True).order_by("order")[:4]),
            "technology_categories": list(TechnologyCategory.objects.prefetch_related("technologies").all()),
            "case_studies": list(CaseStudy.objects.filter(is_active=True).order_by("order")[:2]),
            "completed_projects": list(CaseStudy.objects.filter(is_active=True).order_by("-created_at", "order")[:6]),
            "completed_projects_count": CaseStudy.objects.filter(is_active=True).count(),
            "newsletter": NewsletterSignup.objects.filter(is_active=True).first(),
            "statistics": list(Statistic.objects.filter(is_active=True).order_by("order")[:4]),
            "blog_posts": list(BlogPost.objects.filter(is_published=True).order_by("-publish_date")[:2]),
            "partners": list(Partner.objects.filter(is_active=True).order_by("order")),
            "awards": list(Award.objects.filter(is_active=True).order_by("-year", "order")[:3]),
            "contact_cta": ContactCTA.objects.filter(is_active=True).first(),
        }
        cache.set(HOME_CONTEXT_CACHE_KEY, context, HOME_CONTEXT_CACHE_TTL)
    hero = context.get("hero")
    hero_title = hero.title if hero else "Living Up To Your Creative Potential"
    hero_subtitle = hero.subtitle if hero else "We are an engineering and consulting partner for digital products, data platforms, automation, and enterprise transformation."
    home_ab = _resolve_home_ab_variant(request, hero_title, hero_subtitle)
    services_for_keywords = context.get("services", [])
    industries_for_keywords = context.get("industries", [])
    case_studies_for_keywords = context.get("case_studies", [])
    home_schemas = []
    featured_services = services_for_keywords
    if featured_services:
        home_schemas.append({
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": "Featured Services",
            "itemListElement": [_service_schema(request, service, index + 1) for index, service in enumerate(featured_services)],
        })

    dynamic_keywords = _build_keywords(
        [item.title for item in services_for_keywords[:6]],
        [item.name for item in industries_for_keywords[:5]],
        [item.title for item in case_studies_for_keywords[:4]],
    )

    page_context = {
        **context,
        "home_ab": home_ab,
        **_seo_context(
            request,
            title=f"{home_ab['headline']} | Nexalix Technologies",
            description=home_ab["subtitle"],
            keywords=dynamic_keywords,
            image_url=(hero.video_poster.url if hero and hero.video_poster else ""),
            schemas=home_schemas,
        ),
    }
    return render(request, "home.html", page_context)

def about(request):
    """About page view"""
    about_sections = AboutSection.objects.filter(is_active=True)
    primary_about = about_sections.first()
    context = {
        "about_sections": about_sections,
        "primary_about": primary_about,
    }
    about_title = "About Nexalix | IT & Innovation Consulting"
    about_description = _text_excerpt(
        primary_about.content if primary_about else "Learn about Nexalix Technologies, our mission, and how we deliver enterprise-grade IT and innovation consulting.",
        limit=160,
    )
    context.update(_seo_context(
        request,
        title=about_title,
        description=about_description,
    ))
    return render(request, "about.html", context)

def services(request):
    """Services list page view"""
    # Get all active services, ordered by order field
    services_list = list(Service.objects.filter(is_active=True).order_by('order'))
    
    # Group services by category
    services_by_category = {}
    for service in services_list:
        category = service.get_category_display()
        if category not in services_by_category:
            services_by_category[category] = []
        services_by_category[category].append(service)
    
    
    pricing_plans = PricingPlan.objects.all().order_by('order')
    
    dynamic_description = "Explore our comprehensive range of technology consulting and engineering services."
    if services_list:
        dynamic_description = (
            f"Explore {len(services_list)} consulting and engineering services from Nexalix, including "
            + ", ".join([service.title for service in services_list[:4]])
            + "."
        )
    services_schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Nexalix Service Catalog",
        "itemListElement": [_service_schema(request, service, index + 1) for index, service in enumerate(services_list)],
    }

    context = {
        'services': services_list,
        'services_by_category': services_by_category,
        'pricing_plans': pricing_plans,  # This will work now
        'page_title': 'Our Services',
        'meta_description': dynamic_description,
    }
    context.update(_seo_context(
        request,
        title="Services | Nexalix Technologies",
        description=dynamic_description,
        keywords=_build_keywords([service.title for service in services_list[:10]], "it consulting", "automation systems"),
        schemas=[services_schema],
    ))
    return render(request, 'services.html', context) 

def service_detail(request, slug):
    """Individual service detail page view"""
    service = get_object_or_404(Service, slug=slug, is_active=True)
    
    # Get features and technologies using model methods
    context = {
        'service': service,
        'features': service.get_key_features_list(),  # Using model method
        'technologies': service.get_technologies_list(),  # Using model method
        'pricing_plans': PricingPlan.objects.filter(service=service),  # If you have this model
        'page_title': service.meta_title or service.title,
        'meta_description': service.meta_description or service.short_description,
    }
    context.update(_seo_context(
        request,
        title=f"{service.title} | Nexalix Services",
        description=service.meta_description or service.short_description or service.full_description,
        og_type="article",
        image_url=(service.featured_image.url if service.featured_image else ""),
        schemas=[{"@context": "https://schema.org", **_service_schema(request, service)}],
    ))
    return render(request, 'service_detail.html', context)  # Changed from 'services/detail.html'

def industries(request):
    """Industries page view"""
    industries_list = list(Industry.objects.filter(is_active=True).order_by('order'))
    context = {"industries": industries_list}
    description = "Explore the industries where Nexalix delivers digital transformation solutions."
    if industries_list:
        description = "Industries we support: " + ", ".join([industry.name for industry in industries_list])
    context.update(_seo_context(
        request,
        title="Industries | Nexalix Technologies",
        description=description,
        keywords=_build_keywords([industry.name for industry in industries_list], "industry technology solutions"),
    ))
    return render(request, 'industries.html', context)

def how_we_work(request):
    """How We Work page view"""
    steps = ProcessStep.objects.all().order_by('order')
    context = {"process_steps": steps}
    context.update(_seo_context(
        request,
        title="How We Work | Nexalix Technologies",
        description="Discover the Nexalix delivery process from discovery and planning to implementation, launch, and continuous support.",
    ))
    return render(request, 'how_we_work.html', context)

def why_choose_us(request):
    """Why Choose Us page view"""
    context = {}
    context.update(_seo_context(
        request,
        title="Why Choose Us | Nexalix Technologies",
        description="See why organizations choose Nexalix for IT consulting, engineering delivery, and innovation execution.",
    ))
    return render(request, 'why_choose_us.html', context)


@user_passes_test(is_staff_user, login_url="/admin/login/")
def activity_dashboard(request):
    """Custom staff dashboard showing site activity."""
    requested_period = request.GET.get("period") or request.POST.get("period", "7")
    valid_periods = {"7": 7, "30": 30, "90": 90}
    period_days = valid_periods.get(requested_period, 7)
    search_query = (request.GET.get("q") or request.POST.get("q") or "").strip()
    activity_filter = (request.GET.get("activity") or request.POST.get("activity") or "all").strip().lower()
    if activity_filter not in {"all", "contact", "quote"}:
        activity_filter = "all"
    role_view = (request.GET.get("role") or request.POST.get("role") or "all").strip().lower()
    selected_day_str = (request.GET.get("day") or request.POST.get("day") or "").strip()
    selected_day = _safe_parse_iso_date(selected_day_str)
    if selected_day is None:
        selected_day_str = ""

    allowed_roles = _allowed_role_views(request.user)
    if role_view not in allowed_roles:
        role_view = allowed_roles[0]

    if request.GET.get("saved_filter"):
        saved_filter = DashboardSavedFilter.objects.filter(
            id=request.GET.get("saved_filter"),
            user=request.user,
        ).first()
        if saved_filter:
            return redirect(
                f"{reverse('activity_dashboard')}?{_dashboard_query_string(saved_filter.period_days, saved_filter.activity_filter, saved_filter.search_query, saved_filter.role_view)}"
            )
        messages.error(request, "Saved filter not found.")
        return redirect(f"{reverse('activity_dashboard')}?{_dashboard_query_string(period_days, activity_filter, search_query, role_view, selected_day_str)}")

    if request.method == "POST":
        action = (request.POST.get("action") or "").strip()
        post_period_days = valid_periods.get(request.POST.get("period", str(period_days)), period_days)
        post_search = (request.POST.get("q", search_query) or "").strip()
        post_activity = (request.POST.get("activity", activity_filter) or "all").strip().lower()
        if post_activity not in {"all", "contact", "quote"}:
            post_activity = "all"
        post_role = (request.POST.get("role", role_view) or "all").strip().lower()
        if post_role not in allowed_roles:
            post_role = allowed_roles[0]
        post_day = (request.POST.get("day", selected_day_str) or "").strip()
        if _safe_parse_iso_date(post_day) is None:
            post_day = ""

        if action == "update_profile":
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            email = request.POST.get("email", "").strip()

            if email and "@" not in email:
                messages.error(request, "Please provide a valid email address.")
            else:
                request.user.first_name = first_name
                request.user.last_name = last_name
                request.user.email = email
                request.user.save(update_fields=["first_name", "last_name", "email"])
                messages.success(request, "Admin profile updated successfully.")

        elif action == "save_filter":
            filter_name = (request.POST.get("filter_name") or "").strip()
            if not filter_name:
                messages.error(request, "Enter a name for the saved filter.")
            else:
                DashboardSavedFilter.objects.update_or_create(
                    user=request.user,
                    name=filter_name[:80],
                    defaults={
                        "period_days": post_period_days,
                        "activity_filter": post_activity,
                        "role_view": post_role,
                        "search_query": post_search[:200],
                    },
                )
                messages.success(request, f'Saved filter "{filter_name[:80]}" updated.')

        elif action == "delete_saved_filter":
            saved_filter_id = request.POST.get("saved_filter_id")
            deleted, _ = DashboardSavedFilter.objects.filter(
                id=saved_filter_id,
                user=request.user,
            ).delete()
            if deleted:
                messages.success(request, "Saved filter deleted.")
            else:
                messages.error(request, "Saved filter was not found.")

        return redirect(
            f"{reverse('activity_dashboard')}?{_dashboard_query_string(post_period_days, post_activity, post_search, post_role, post_day)}"
        )

    now = timezone.now()
    window_start = now - timedelta(days=period_days)

    contacts_queryset = ContactMessage.objects.all()
    quotes_queryset = QuoteRequest.objects.select_related("service")
    if role_view == "ops":
        contacts_queryset = contacts_queryset.filter(is_read=False)
        quotes_queryset = quotes_queryset.filter(status__in=["new", "reviewed", "sent"])
    elif role_view == "sales":
        quotes_queryset = quotes_queryset.exclude(status="lost")

    recent_contacts_period = contacts_queryset.filter(submitted_at__gte=window_start)
    recent_quotes_period = quotes_queryset.filter(created_at__gte=window_start)

    aggregates_cache_key = get_dashboard_aggregate_cache_key(period_days)
    cached_aggregates = cache.get(aggregates_cache_key) if not search_query and role_view == "all" else None

    if cached_aggregates:
        kpis = cached_aggregates["kpis"]
        trend_data = cached_aggregates["trend_data"]
    else:
        contacts_totals = contacts_queryset.aggregate(
            total=Count("id"),
            unread=Count("id", filter=Q(is_read=False)),
            window=Count("id", filter=Q(submitted_at__gte=window_start)),
        )
        quotes_totals = quotes_queryset.aggregate(
            total=Count("id"),
            new=Count("id", filter=Q(status="new")),
            window=Count("id", filter=Q(created_at__gte=window_start)),
        )
        kpis = {
            "contacts_total": contacts_totals["total"],
            "contacts_unread": contacts_totals["unread"],
            "contacts_window": contacts_totals["window"],
            "quotes_total": quotes_totals["total"],
            "quotes_new": quotes_totals["new"],
            "quotes_window": quotes_totals["window"],
        }

        trend_contacts = recent_contacts_period
        trend_quotes = recent_quotes_period
        if search_query:
            trend_contacts = trend_contacts.filter(
                Q(full_name__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(service__icontains=search_query)
                | Q(message__icontains=search_query)
            )
            trend_quotes = trend_quotes.filter(
                Q(quote_reference__icontains=search_query)
                | Q(full_name__icontains=search_query)
                | Q(email__icontains=search_query)
                | Q(company__icontains=search_query)
                | Q(project_summary__icontains=search_query)
                | Q(service__title__icontains=search_query)
            )

        contacts_daily_raw = trend_contacts.annotate(day=TruncDate("submitted_at")).values("day").annotate(total=Count("id"))
        quotes_daily_raw = trend_quotes.annotate(day=TruncDate("created_at")).values("day").annotate(total=Count("id"))
        contacts_daily = {item["day"]: item["total"] for item in contacts_daily_raw}
        quotes_daily = {item["day"]: item["total"] for item in quotes_daily_raw}

        trend_days = [window_start.date() + timedelta(days=i) for i in range(period_days)]
        max_count = max(
            max(contacts_daily.values(), default=0),
            max(quotes_daily.values(), default=0),
            1,
        )
        trend_data = []
        for day in trend_days:
            contact_count = contacts_daily.get(day, 0)
            quote_count = quotes_daily.get(day, 0)
            trend_data.append({
                "label": day.strftime("%b %d"),
                "date": day.isoformat(),
                "contacts": contact_count,
                "quotes": quote_count,
                "contacts_height": max(6, int((contact_count / max_count) * 120)) if contact_count else 4,
                "quotes_height": max(6, int((quote_count / max_count) * 120)) if quote_count else 4,
            })

        if not search_query and role_view == "all":
            cache.set(
                aggregates_cache_key,
                {"kpis": kpis, "trend_data": trend_data},
                DASHBOARD_AGGREGATES_CACHE_TTL,
            )

    filtered_contacts = recent_contacts_period
    filtered_quotes = recent_quotes_period
    if search_query:
        filtered_contacts = filtered_contacts.filter(
            Q(full_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(service__icontains=search_query)
            | Q(message__icontains=search_query)
        )
        filtered_quotes = filtered_quotes.filter(
            Q(quote_reference__icontains=search_query)
            | Q(full_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(company__icontains=search_query)
            | Q(project_summary__icontains=search_query)
            | Q(service__title__icontains=search_query)
        )
    if selected_day:
        filtered_contacts = filtered_contacts.filter(submitted_at__date=selected_day)
        filtered_quotes = filtered_quotes.filter(created_at__date=selected_day)

    sla_summary, sla_queue = _build_sla_snapshot(filtered_contacts, filtered_quotes, now)
    funnel_analytics = _safe_funnel_analytics(filtered_contacts, filtered_quotes)
    alert_summary, alerts = _safe_alert_center(now, contacts_queryset, quotes_queryset, sla_summary)
    quality_summary, quality_issues = _safe_data_quality(now, filtered_contacts, filtered_quotes)

    client_activities = _build_client_activities(filtered_contacts, filtered_quotes, role_view, limit=60)
    if activity_filter in {"contact", "quote"}:
        client_activities = [item for item in client_activities if item["type"] == activity_filter]

    action_labels = {
        ADDITION: "Added",
        CHANGE: "Updated",
        DELETION: "Deleted",
    }
    action_styles = {
        ADDITION: "added",
        CHANGE: "updated",
        DELETION: "deleted",
    }
    logs_queryset = LogEntry.objects.none()
    if role_view != "sales":
        logs_queryset = LogEntry.objects.select_related("user", "content_type").order_by("-action_time")
        if search_query:
            logs_queryset = logs_queryset.filter(
                Q(object_repr__icontains=search_query)
                | Q(user__username__icontains=search_query)
                | Q(change_message__icontains=search_query)
                | Q(content_type__model__icontains=search_query)
            )
        if selected_day:
            logs_queryset = logs_queryset.filter(action_time__date=selected_day)

    admin_logs = []
    for entry in logs_queryset[:40]:
        model_name = "Unknown"
        if entry.content_type:
            model_class = entry.content_type.model_class()
            if model_class:
                model_name = model_class._meta.verbose_name.title()
        admin_logs.append({
            "time": entry.action_time,
            "user": entry.user.get_username(),
            "action": action_labels.get(entry.action_flag, "Changed"),
            "style": action_styles.get(entry.action_flag, "updated"),
            "object_label": entry.object_repr,
            "model": model_name,
            "link": entry.get_admin_url(),
            "search_text": f"{entry.user.get_username()} {model_name} {entry.object_repr} {entry.change_message}".lower(),
        })

    export_type = (request.GET.get("export") or "").strip().lower()
    export_format = (request.GET.get("format") or "").strip().lower()
    if export_type == "executive":
        try:
            weekly_snapshot = _build_weekly_exec_snapshot(now, role_view=role_view)
            if export_format == "pdf":
                return _weekly_report_pdf_response(weekly_snapshot)
            return _weekly_report_csv_response(weekly_snapshot)
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception("Executive report generation failed: %s", exc)
            messages.error(request, "Executive report generation failed. Please try again.")

    if request.GET.get("export") == "csv":
        dataset = (request.GET.get("dataset") or "activity").strip().lower()
        response = HttpResponse(content_type="text/csv")
        ts = timezone.now().strftime("%Y%m%d_%H%M")
        response["Content-Disposition"] = f'attachment; filename="nexalix_{dataset}_{ts}.csv"'
        writer = csv.writer(response)
        if dataset == "logs":
            writer.writerow(["Time", "User", "Action", "Model", "Object"])
            for log in admin_logs:
                writer.writerow([
                    timezone.localtime(log["time"]).strftime("%Y-%m-%d %H:%M"),
                    log["user"],
                    log["action"],
                    log["model"],
                    log["object_label"],
                ])
        else:
            writer.writerow(["Type", "Timestamp", "Title", "Subtitle", "Detail", "Status", "Admin URL"])
            for item in client_activities:
                writer.writerow([
                    item["type"],
                    timezone.localtime(item["timestamp"]).strftime("%Y-%m-%d %H:%M"),
                    item["title"],
                    item["subtitle"],
                    item["detail"],
                    item["status"],
                    request.build_absolute_uri(item["admin_url"]),
                ])
        return response

    saved_filters = DashboardSavedFilter.objects.filter(user=request.user)
    saved_filter_entries = []
    for saved in saved_filters:
        saved_filter_entries.append({
            "id": saved.id,
            "name": saved.name,
            "period_days": saved.period_days,
            "activity_filter": saved.activity_filter,
            "role_view": saved.role_view,
            "search_query": saved.search_query,
            "apply_query": _dashboard_query_string(
                saved.period_days,
                saved.activity_filter,
                saved.search_query,
                saved.role_view,
            ),
        })

    period_options = [
        {
            "days": day_count,
            "query": _dashboard_query_string(day_count, activity_filter, search_query, role_view, selected_day_str),
            "active": period_days == day_count,
        }
        for day_count in (7, 30, 90)
    ]
    role_switches = [
        {
            "key": value,
            "label": ROLE_LABELS.get(value, value.title()),
            "query": _dashboard_query_string(period_days, activity_filter, search_query, value, selected_day_str),
        }
        for value in allowed_roles
    ]
    current_query = _dashboard_query_string(period_days, activity_filter, search_query, role_view, selected_day_str)

    contacts_preview = filtered_contacts.order_by("-submitted_at")[:8]
    quotes_preview = filtered_quotes.order_by("-created_at")[:8]
    partners_preview = Partner.objects.filter(is_active=True).order_by("order", "name")[:8]
    case_studies_preview = CaseStudy.objects.filter(is_active=True).order_by("order", "-created_at")[:8]
    seo_topics_preview = generate_seo_topics(DEFAULT_SEO_KEYWORDS[:4], 1)

    return render(request, "admin/activity_dashboard.html", {
        "kpis": kpis,
        "period_days": period_days,
        "client_activities": client_activities,
        "admin_logs": admin_logs,
        "trend_data": trend_data,
        "search_query": search_query,
        "activity_filter": activity_filter,
        "role_view": role_view,
        "period_options": period_options,
        "role_switches": role_switches,
        "saved_filters": saved_filter_entries,
        "current_query": current_query,
        "selected_day": selected_day,
        "selected_day_str": selected_day_str,
        "selected_day_label": selected_day.strftime("%b %d, %Y") if selected_day else "",
        "csv_activity_query": f"{current_query}&export=csv&dataset=activity",
        "csv_logs_query": f"{current_query}&export=csv&dataset=logs",
        "weekly_csv_query": f"{current_query}&export=executive&format=csv",
        "weekly_pdf_query": f"{current_query}&export=executive&format=pdf",
        "clear_day_query": _dashboard_query_string(period_days, activity_filter, search_query, role_view),
        "sales_mode": role_view == "sales",
        "ops_mode": role_view == "ops",
        "contacts_preview": contacts_preview,
        "quotes_preview": quotes_preview,
        "partners_preview": partners_preview,
        "case_studies_preview": case_studies_preview,
        "seo_keywords_preview": DEFAULT_SEO_KEYWORDS[:8],
        "seo_topics_preview": seo_topics_preview,
        "sla_summary": sla_summary,
        "sla_queue": sla_queue,
        "contact_sla_hours": DASHBOARD_CONTACT_SLA_HOURS,
        "quote_sla_hours": DASHBOARD_QUOTE_SLA_HOURS,
        "funnel_analytics": funnel_analytics,
        "alert_summary": alert_summary,
        "alerts": alerts,
        "quality_summary": quality_summary,
        "quality_issues": quality_issues,
    })


@user_passes_test(is_staff_user, login_url="/admin/login/")
def activity_dashboard_live(request):
    """Polling endpoint for dashboard live updates."""
    requested_period = request.GET.get("period", "7")
    valid_periods = {"7": 7, "30": 30, "90": 90}
    period_days = valid_periods.get(requested_period, 7)

    search_query = (request.GET.get("q") or "").strip()
    role_view = (request.GET.get("role") or "all").strip().lower()
    selected_day_str = (request.GET.get("day") or "").strip()
    selected_day = _safe_parse_iso_date(selected_day_str)

    allowed_roles = _allowed_role_views(request.user)
    if role_view not in allowed_roles:
        role_view = allowed_roles[0]

    now = timezone.now()
    window_start = now - timedelta(days=period_days)

    contacts_queryset = ContactMessage.objects.all()
    quotes_queryset = QuoteRequest.objects.select_related("service")
    if role_view == "ops":
        contacts_queryset = contacts_queryset.filter(is_read=False)
        quotes_queryset = quotes_queryset.filter(status__in=["new", "reviewed", "sent"])
    elif role_view == "sales":
        quotes_queryset = quotes_queryset.exclude(status="lost")

    recent_contacts_period = contacts_queryset.filter(submitted_at__gte=window_start)
    recent_quotes_period = quotes_queryset.filter(created_at__gte=window_start)

    contacts_totals = contacts_queryset.aggregate(
        total=Count("id"),
        unread=Count("id", filter=Q(is_read=False)),
        window=Count("id", filter=Q(submitted_at__gte=window_start)),
    )
    quotes_totals = quotes_queryset.aggregate(
        total=Count("id"),
        new=Count("id", filter=Q(status="new")),
        window=Count("id", filter=Q(created_at__gte=window_start)),
    )
    kpis = {
        "contacts_total": contacts_totals["total"],
        "contacts_unread": contacts_totals["unread"],
        "contacts_window": contacts_totals["window"],
        "quotes_total": quotes_totals["total"],
        "quotes_new": quotes_totals["new"],
        "quotes_window": quotes_totals["window"],
    }

    filtered_contacts = recent_contacts_period
    filtered_quotes = recent_quotes_period
    if search_query:
        filtered_contacts = filtered_contacts.filter(
            Q(full_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(service__icontains=search_query)
            | Q(message__icontains=search_query)
        )
        filtered_quotes = filtered_quotes.filter(
            Q(quote_reference__icontains=search_query)
            | Q(full_name__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(company__icontains=search_query)
            | Q(project_summary__icontains=search_query)
            | Q(service__title__icontains=search_query)
        )
    if selected_day:
        filtered_contacts = filtered_contacts.filter(submitted_at__date=selected_day)
        filtered_quotes = filtered_quotes.filter(created_at__date=selected_day)

    sla_summary, sla_queue = _build_sla_snapshot(filtered_contacts, filtered_quotes, now)
    funnel_analytics = _safe_funnel_analytics(filtered_contacts, filtered_quotes)
    alert_summary, alerts = _safe_alert_center(now, contacts_queryset, quotes_queryset, sla_summary)
    quality_summary, quality_issues = _safe_data_quality(now, filtered_contacts, filtered_quotes)
    client_activities = _build_client_activities(filtered_contacts, filtered_quotes, role_view, limit=30)

    try:
        payload_activities = [
            {
                "type": item["type"],
                "title": item["title"],
                "subtitle": item["subtitle"],
                "detail": item["detail"],
                "status": item["status"],
                "admin_url": item["admin_url"],
                "timestamp_label": timezone.localtime(item["timestamp"]).strftime("%b %d, %Y %H:%M"),
                "search_text": item["search_text"],
            }
            for item in client_activities
        ]
        payload_sla_queue = [
            {
                "kind": item["kind"],
                "title": item["title"],
                "subtitle": item["subtitle"],
                "status": item["status"],
                "admin_url": item["admin_url"],
                "due_at_label": item["due_at_label"],
                "remaining_label": item["remaining_label"],
                "bucket": item["bucket"],
            }
            for item in sla_queue
        ]
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Dashboard live payload build failed: %s", exc)
        payload_activities = []
        payload_sla_queue = []
    payload_alerts = [
        {
            "severity": item["severity"],
            "title": item["title"],
            "message": item["message"],
            "action_url": item["action_url"],
        }
        for item in alerts
    ]
    payload_quality = [
        {
            "severity": item["severity"],
            "category": item["category"],
            "label": item["label"],
            "detail": item["detail"],
            "action_url": item["action_url"],
        }
        for item in quality_issues[:12]
    ]

    contacts_pct = _safe_ratio_percent(kpis["contacts_window"], kpis["contacts_total"])
    quotes_pct = _safe_ratio_percent(kpis["quotes_window"], kpis["quotes_total"])
    unread_pct = _safe_ratio_percent(kpis["contacts_unread"], kpis["contacts_total"])
    new_quotes_pct = _safe_ratio_percent(kpis["quotes_new"], kpis["quotes_total"])

    return JsonResponse({
        "ok": True,
        "server_time": timezone.localtime(now).strftime("%Y-%m-%d %H:%M:%S"),
        "kpis": kpis,
        "kpi_percentages": {
            "contacts_window": contacts_pct,
            "quotes_window": quotes_pct,
            "contacts_unread": unread_pct,
            "quotes_new": new_quotes_pct,
        },
        "sla_summary": sla_summary,
        "sla_queue": payload_sla_queue,
        "client_activities": payload_activities,
        "funnel_analytics": funnel_analytics,
        "alert_summary": alert_summary,
        "alerts": payload_alerts,
        "quality_summary": quality_summary,
        "quality_issues": payload_quality,
    })


@user_passes_test(is_staff_user, login_url="/admin/login/")
def seo_topic_generator(request):
    """Staff tool to generate SEO blog topic ideas and optionally save drafts."""
    default_keywords_text = "\n".join(DEFAULT_SEO_KEYWORDS)
    keywords_text = default_keywords_text
    topics_per_keyword = 5
    generated_topics = []

    if request.method == "POST":
        keywords_text = request.POST.get("keywords", default_keywords_text)
        raw_per_keyword = request.POST.get("topics_per_keyword", "5")
        action = (request.POST.get("action") or "generate").strip().lower()
        try:
            topics_per_keyword = int(raw_per_keyword)
        except (TypeError, ValueError):
            topics_per_keyword = 5
        topics_per_keyword = max(1, min(topics_per_keyword, 8))

        parsed_keywords = parse_keywords(keywords_text)
        if not parsed_keywords:
            messages.error(request, "Please provide at least one keyword.")
        else:
            generated_topics = generate_seo_topics(parsed_keywords, topics_per_keyword)

            if action == "save":
                created_count = 0
                skipped_count = 0
                today = timezone.now().date()

                for topic in generated_topics:
                    title = topic["title"]
                    if BlogPost.objects.filter(title=title).exists():
                        skipped_count += 1
                        continue

                    base_slug = slugify(title)[:44] or "nexalix-seo-topic"
                    candidate_slug = base_slug
                    suffix = 2
                    while BlogPost.objects.filter(slug=candidate_slug).exists():
                        token = f"-{suffix}"
                        candidate_slug = f"{base_slug[:50 - len(token)]}{token}"
                        suffix += 1

                    BlogPost.objects.create(
                        title=title,
                        slug=candidate_slug,
                        excerpt=topic["meta_description"],
                        content=build_draft_content(topic),
                        publish_date=today,
                        is_published=False,
                    )
                    created_count += 1

                if created_count:
                    messages.success(
                        request,
                        f"Created {created_count} draft blog posts from generated topics.",
                    )
                if skipped_count:
                    messages.warning(
                        request,
                        f"Skipped {skipped_count} topics because matching titles already exist.",
                    )

    return render(
        request,
        "admin/seo_topic_generator.html",
        {
            "keywords_text": keywords_text,
            "topics_per_keyword": topics_per_keyword,
            "generated_topics": generated_topics,
        },
    )


def quote_generator(request):
    """Auto Quote Generator page view"""
    quote_services = Service.objects.filter(
        is_active=True,
        show_in_quote_generator=True
    ).order_by("order", "title")
    quote_addons = QuoteAddon.objects.filter(is_active=True).order_by("order", "name")

    success_message = None
    error_message = None
    generated_quote = None
    form_data = {
        "full_name": "",
        "email": "",
        "company": "",
        "phone": "",
        "service": "",
        "complexity": "growth",
        "timeline": "standard",
        "support_plan": "none",
        "project_summary": "",
        "addons": [],
    }

    if request.method == "POST":
        form_data = {
            "full_name": request.POST.get("full_name", "").strip(),
            "email": request.POST.get("email", "").strip(),
            "company": request.POST.get("company", "").strip(),
            "phone": request.POST.get("phone", "").strip(),
            "service": request.POST.get("service", "").strip(),
            "complexity": request.POST.get("complexity", "growth").strip(),
            "timeline": request.POST.get("timeline", "standard").strip(),
            "support_plan": request.POST.get("support_plan", "none").strip(),
            "project_summary": request.POST.get("project_summary", "").strip(),
            "addons": request.POST.getlist("addons"),
        }

        if not form_data["full_name"] or not form_data["email"] or not form_data["service"] or not form_data["project_summary"]:
            error_message = "Please fill in all required fields to generate your quote."
        else:
            service = Service.objects.filter(
                id=form_data["service"],
                is_active=True,
                show_in_quote_generator=True
            ).first()

            if not service:
                error_message = "Selected service is unavailable. Please choose another option."
            else:
                selected_addons = list(quote_addons.filter(id__in=form_data["addons"]))
                estimate = calculate_quote_estimate(
                    service=service,
                    complexity=form_data["complexity"],
                    timeline=form_data["timeline"],
                    support_plan=form_data["support_plan"],
                    addons=selected_addons,
                )

                quote_request = QuoteRequest.objects.create(
                    full_name=form_data["full_name"],
                    email=form_data["email"],
                    company=form_data["company"],
                    phone=form_data["phone"],
                    service=service,
                    complexity=form_data["complexity"],
                    timeline=form_data["timeline"],
                    support_plan=form_data["support_plan"],
                    project_summary=form_data["project_summary"],
                    currency="USD",
                    estimated_subtotal=estimate["subtotal"],
                    addons_total=estimate["addons_total"],
                    support_total=estimate["support_total"],
                    estimated_total=estimate["total"],
                    estimated_min=estimate["min_estimate"],
                    estimated_max=estimate["max_estimate"],
                    estimated_weeks=estimate["estimated_weeks"],
                )
                quote_request.selected_addons.set(selected_addons)

                send_quote_notifications(quote_request)

                generated_quote = {
                    "reference": quote_request.quote_reference,
                    "subtotal": quote_request.estimated_subtotal,
                    "addons_total": quote_request.addons_total,
                    "support_total": quote_request.support_total,
                    "total": quote_request.estimated_total,
                    "min_estimate": quote_request.estimated_min,
                    "max_estimate": quote_request.estimated_max,
                    "estimated_weeks": quote_request.estimated_weeks,
                }

                success_message = f"Quote generated successfully. Reference: {quote_request.quote_reference}."
                form_data = {
                    "full_name": "",
                    "email": "",
                    "company": "",
                    "phone": "",
                    "service": "",
                    "complexity": "growth",
                    "timeline": "standard",
                    "support_plan": "none",
                    "project_summary": "",
                    "addons": [],
                }

    complexity_options = []
    for value, label in QuoteRequest.COMPLEXITY_CHOICES:
        complexity_options.append({
            "value": value,
            "label": label,
            "multiplier": str(COMPLEXITY_MULTIPLIERS.get(value, Decimal("1.00"))),
            "weeks_multiplier": str(COMPLEXITY_DURATION.get(value, Decimal("1.00"))),
        })

    timeline_options = []
    for value, label in QuoteRequest.TIMELINE_CHOICES:
        timeline_options.append({
            "value": value,
            "label": label,
            "multiplier": str(TIMELINE_MULTIPLIERS.get(value, Decimal("1.00"))),
            "weeks_multiplier": str(TIMELINE_DURATION.get(value, Decimal("1.00"))),
        })

    support_options = []
    for value, label in QuoteRequest.SUPPORT_CHOICES:
        support_options.append({
            "value": value,
            "label": label,
            "multiplier": str(SUPPORT_MULTIPLIERS.get(value, Decimal("0.00"))),
        })

    context = {
        "quote_services": quote_services,
        "quote_addons": quote_addons,
        "complexity_options": complexity_options,
        "timeline_options": timeline_options,
        "support_options": support_options,
        "success_message": success_message,
        "error_message": error_message,
        "generated_quote": generated_quote,
        "form_data": form_data,
    }
    context.update(_seo_context(
        request,
        title="Auto Quote Generator | Nexalix Technologies",
        description="Generate a fast estimate for your software, cloud, AI, or consulting project using Nexalix Auto Quote Generator.",
    ))
    return render(request, "quote_generator.html", context)


def send_quote_notifications(quote_request):
    try:
        configured_recipients = getattr(settings, "ADMIN_EMAILS", [])
        if isinstance(configured_recipients, str):
            configured_recipients = [
                email.strip()
                for email in configured_recipients.split(",")
                if email.strip()
            ]

        admin_emails = list(configured_recipients)
        contact_notification_email = getattr(
            settings,
            "CONTACT_NOTIFICATION_EMAIL",
            "dachiek4@gmail.com",
        ).strip()
        if contact_notification_email and contact_notification_email not in admin_emails:
            admin_emails.append(contact_notification_email)
        if not admin_emails:
            admin_emails = ["dachiek4@gmail.com"]

        selected_addons = ", ".join(
            quote_request.selected_addons.values_list("name", flat=True)
        ) or "None"
        subject = f"New Auto Quote Request: {quote_request.quote_reference}"
        body = f"""
Quote Reference: {quote_request.quote_reference}
Name: {quote_request.full_name}
Email: {quote_request.email}
Company: {quote_request.company or 'Not provided'}
Phone: {quote_request.phone or 'Not provided'}
Service: {quote_request.service.title if quote_request.service else 'Not selected'}
Complexity: {quote_request.get_complexity_display()}
Timeline: {quote_request.get_timeline_display()}
Support Plan: {quote_request.get_support_plan_display()}
Add-ons: {selected_addons}
Estimated Total: {quote_request.currency} {quote_request.estimated_total}
Range: {quote_request.currency} {quote_request.estimated_min} - {quote_request.currency} {quote_request.estimated_max}
Estimated Delivery: ~{quote_request.estimated_weeks} weeks

Project Summary:
{quote_request.project_summary}
        """
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=True,
        )

        user_subject = f"Your Nexalix Quote ({quote_request.quote_reference})"
        user_body = f"""
Hi {quote_request.full_name},

Thank you for using our Auto Quote Generator.

Quote Reference: {quote_request.quote_reference}
Estimated Budget: {quote_request.currency} {quote_request.estimated_min} - {quote_request.currency} {quote_request.estimated_max}
Estimated Timeline: ~{quote_request.estimated_weeks} weeks

Our team will review your request and follow up with a detailed proposal.
        """
        send_mail(
            subject=user_subject,
            message=user_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[quote_request.email],
            fail_silently=True,
        )
    except Exception as exc:
        logger.exception("Error sending quote notifications: %s", exc)



def _ensure_session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key or ""


def _get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _rate_limit_hit(scope, request, max_requests, window_seconds):
    session_key = _ensure_session_key(request) or "anonymous"
    ip_address = _get_client_ip(request)
    cache_key = f"chatbot:{scope}:{session_key}:{ip_address}"

    current = cache.get(cache_key, 0)
    if current >= max_requests:
        return True

    cache.set(cache_key, current + 1, timeout=window_seconds)
    return False


def _load_chatbot_history(request):
    history = request.session.get(CHATBOT_HISTORY_SESSION_KEY, [])
    if not isinstance(history, list):
        return []
    cleaned = []
    for item in history[-CHATBOT_HISTORY_MAX_ITEMS:]:
        role = item.get("role") if isinstance(item, dict) else ""
        content = item.get("content") if isinstance(item, dict) else ""
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            cleaned.append({"role": role, "content": content.strip()[:1800]})
    return cleaned


def _save_chatbot_history(request, history):
    request.session[CHATBOT_HISTORY_SESSION_KEY] = history[-CHATBOT_HISTORY_MAX_ITEMS:]
    request.session.modified = True


def _validate_chat_message(message):
    message = (message or "").strip()
    if len(message) < 2:
        return "", "Please provide a little more detail in your message."
    if len(message) > 1200:
        return "", "Message is too long. Please keep it under 1200 characters."
    return message, ""


def _validate_lead_payload(payload):
    name = (payload.get("name") or payload.get("full_name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    phone = (payload.get("phone") or "").strip()
    company = (payload.get("company") or "").strip()
    project_needs = (payload.get("project_needs") or payload.get("project_description") or "").strip()
    source_page = (payload.get("source_page") or "").strip()
    service_interest = payload.get("service_interest") or ""
    assistant_summary = (payload.get("assistant_summary") or "").strip()
    escalate_channel = (payload.get("escalation_channel") or "none").strip().lower()

    if not name or len(name) < 2:
        return None, "Please provide a valid full name."
    if len(name) > 200:
        return None, "Full name is too long."

    email_validator = EmailValidator()
    try:
        email_validator(email)
    except ValidationError:
        return None, "Please provide a valid email address."

    if phone:
        phone_pattern = re.compile(r"^[0-9+()\\-\\s]{7,25}$")
        if not phone_pattern.match(phone):
            return None, "Please provide a valid phone number."

    if company and len(company) > 200:
        return None, "Company name is too long."

    if not project_needs or len(project_needs) < 10:
        return None, "Please provide project details (at least 10 characters)."
    if len(project_needs) > 3000:
        return None, "Project details are too long. Keep them under 3000 characters."

    if isinstance(service_interest, list):
        service_interest = ", ".join(
            str(item).strip() for item in service_interest if str(item).strip()
        )
    service_interest = str(service_interest).strip()[:250]
    if not service_interest:
        return None, "Please select a service of interest."

    allowed_channels = {"none", "whatsapp", "contact", "email"}
    if escalate_channel not in allowed_channels:
        escalate_channel = "none"

    sanitized = {
        "name": name,
        "email": email,
        "phone": phone[:50],
        "company": company,
        "project_needs": project_needs,
        "source_page": source_page[:255],
        "interested_services": service_interest,
        "assistant_summary": assistant_summary[:1200],
        "escalation_channel": escalate_channel,
    }
    return sanitized, ""


def _validate_ux_event_payload(payload):
    event_type = (payload.get("event_type") or "").strip().lower()
    label = (payload.get("label") or "").strip()
    metadata = payload.get("metadata") or {}
    page_path = (payload.get("page_path") or "").strip()

    allowed_events = {
        "cta_click",
        "search_query",
        "search_result_click",
        "contact_form_submit",
        "quote_form_submit",
        "form_dropoff",
        "chat_open",
        "chat_message_sent",
        "chat_lead_requested",
        "chat_lead_submitted",
        "ab_exposure",
        "ab_click",
    }

    if event_type not in allowed_events:
        return None, "Unsupported event type."

    if not isinstance(metadata, dict):
        metadata = {}

    trimmed_metadata = {}
    for key, value in metadata.items():
        safe_key = str(key).strip()[:60]
        if not safe_key:
            continue
        trimmed_metadata[safe_key] = str(value).strip()[:240]

    validated = {
        "event_type": event_type,
        "label": label[:120],
        "page_path": page_path[:200] or "/",
        "metadata": trimmed_metadata,
    }
    return validated, ""


def _resolve_admin_recipients():
    configured_recipients = getattr(settings, "ADMIN_EMAILS", [])
    if isinstance(configured_recipients, str):
        configured_recipients = [email.strip() for email in configured_recipients.split(",") if email.strip()]

    recipients = list(configured_recipients)
    contact_notification_email = getattr(
        settings,
        "CONTACT_NOTIFICATION_EMAIL",
        "dachiek4@gmail.com",
    ).strip()
    if contact_notification_email and contact_notification_email not in recipients:
        recipients.append(contact_notification_email)
    if not recipients:
        recipients = ["dachiek4@gmail.com"]
    return recipients


def _send_chatbot_lead_notification(lead):
    subject = f"New Chatbot Lead: {lead.full_name}"
    body = f"""
New lead captured from Nexalix chatbot

Name: {lead.full_name}
Email: {lead.email}
Phone: {lead.phone or 'Not provided'}
Company: {lead.company or 'Not provided'}
Interested Services: {lead.interested_services or 'Not provided'}
Escalation: {lead.escalation_channel}
Submitted: {lead.created_at.strftime('%Y-%m-%d %H:%M:%S')}
Source Page: {lead.source_page or 'Unknown'}

Project Needs:
{lead.project_needs}

Assistant Summary:
{lead.assistant_summary or 'Not provided'}
    """.strip()
    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=_resolve_admin_recipients(),
        fail_silently=False,
    )


@require_POST
def chatbot_message_api(request):
    max_requests = int(getattr(settings, "CHATBOT_RATE_LIMIT_COUNT", 20))
    window_seconds = int(getattr(settings, "CHATBOT_RATE_LIMIT_WINDOW_SECONDS", 600))

    if _rate_limit_hit("message", request, max_requests, window_seconds):
        return JsonResponse(
            {"ok": False, "error": "Too many requests. Please wait before sending another message."},
            status=429,
        )

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid request payload."}, status=400)

    message, error = _validate_chat_message(payload.get("message"))
    if error:
        return JsonResponse({"ok": False, "error": error}, status=400)

    history = _load_chatbot_history(request)
    services = Service.objects.filter(is_active=True).order_by("order", "title")[:20]

    quote_url = request.build_absolute_uri(reverse("quote_generator"))
    contact_url = request.build_absolute_uri(reverse("contact"))
    whatsapp_url = getattr(settings, "CHATBOT_WHATSAPP_URL", "https://wa.me/254768774232")

    response_payload = generate_chatbot_response(
        user_message=message,
        history=history,
        services=services,
        quote_url=quote_url,
        contact_url=contact_url,
        whatsapp_url=whatsapp_url,
    )

    assistant_message = (response_payload.get("answer") or "").strip()
    if not assistant_message:
        assistant_message = (
            "I can help with Nexalix services, pricing flow, and project guidance. "
            "Share your use case and I’ll recommend the right next step."
        )

    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": assistant_message})
    _save_chatbot_history(request, history)

    logger.info("Chatbot response generated for session=%s", _ensure_session_key(request))

    return JsonResponse(
        {
            "ok": True,
            "answer": assistant_message,
            "recommended_services": response_payload.get("recommended_services", []),
            "collect_lead": bool(response_payload.get("collect_lead")),
            "escalate_to_human": bool(response_payload.get("escalate_to_human")),
            "escalation_message": response_payload.get("escalation_message", ""),
            "contact_url": contact_url,
            "quote_url": quote_url,
            "whatsapp_url": whatsapp_url,
        }
    )


@require_POST
def chatbot_lead_api(request):
    max_requests = int(getattr(settings, "CHATBOT_LEAD_RATE_LIMIT_COUNT", 6))
    window_seconds = int(getattr(settings, "CHATBOT_LEAD_RATE_LIMIT_WINDOW_SECONDS", 600))

    if _rate_limit_hit("lead", request, max_requests, window_seconds):
        return JsonResponse(
            {"ok": False, "error": "Too many lead submissions. Please wait a few minutes and try again."},
            status=429,
        )

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid request payload."}, status=400)

    validated, error = _validate_lead_payload(payload)
    if error:
        return JsonResponse({"ok": False, "error": error}, status=400)

    session_key = _ensure_session_key(request)

    lead = ChatbotLead.objects.create(
        session_key=session_key,
        full_name=validated["name"],
        email=validated["email"],
        phone=validated["phone"],
        company=validated["company"],
        project_needs=validated["project_needs"],
        interested_services=validated["interested_services"],
        assistant_summary=validated["assistant_summary"],
        source_page=validated["source_page"],
        escalation_channel=validated["escalation_channel"],
        is_escalated=validated["escalation_channel"] != "none",
        metadata={
            "ip_address": _get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", "")[:500],
            "referrer": request.META.get("HTTP_REFERER", "")[:400],
            "source": "website_chatbot",
        },
    )

    email_sent = True
    try:
        _send_chatbot_lead_notification(lead)
    except Exception as exc:
        email_sent = False
        logger.exception("Failed to send chatbot lead email notification: %s", exc)

    logger.info("Chatbot lead created id=%s email=%s", lead.id, lead.email)

    return JsonResponse(
        {
            "ok": True,
            "message": (
                "Thanks. Your details were captured and our team will contact you."
                if email_sent
                else "Thanks. Your details were captured. Our team will still follow up shortly."
            ),
            "lead_id": lead.id,
        }
    )


@csrf_exempt
@require_POST
def ux_event_api(request):
    max_requests = int(getattr(settings, "UX_EVENT_RATE_LIMIT_COUNT", 120))
    window_seconds = int(getattr(settings, "UX_EVENT_RATE_LIMIT_WINDOW_SECONDS", 300))

    if _rate_limit_hit("ux", request, max_requests, window_seconds):
        return JsonResponse({"ok": False, "error": "Rate limit exceeded."}, status=429)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid request payload."}, status=400)

    validated, error = _validate_ux_event_payload(payload)
    if error:
        return JsonResponse({"ok": False, "error": error}, status=400)

    current_day = timezone.localdate().isoformat()
    counter_key = f"ux:event:{current_day}:{validated['event_type']}"
    try:
        cache.incr(counter_key)
    except ValueError:
        cache.set(counter_key, 1, timeout=60 * 60 * 24 * 7)

    logger.info(
        "UX event tracked type=%s label=%s page=%s meta=%s",
        validated["event_type"],
        validated["label"],
        validated["page_path"],
        validated["metadata"],
    )
    return JsonResponse({"ok": True})


def contact(request):
    """Contact page view"""
    success_message = None
    error_message = None
    
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        service = request.POST.get("service", "").strip()
        message = request.POST.get("message", "").strip()
        
        # Basic validation
        if not all([full_name, email, service, message]):
            error_message = "Please fill in all required fields (Name, Email, Service, and Message)."
        elif '@' not in email or '.' not in email:
            error_message = "Please enter a valid email address."
        else:
            try:
                # Save to database
                contact_msg = ContactMessage.objects.create(
                    full_name=full_name,
                    email=email,
                    service=service,
                    message=message
                )
                
                # Send email notification to admin
                admin_email_sent = send_admin_notification(contact_msg)
                
                # Send confirmation to user
                user_email_sent = send_user_confirmation(contact_msg)
                
                if admin_email_sent:
                    success_message = "Thank you for your message! We've received it and will get back to you soon. A confirmation email has been sent to you."
                else:
                    success_message = "Thank you for your message! We've received it (email notification failed, but your message was saved)."
                
            except Exception as e:
                logger.exception("Error saving contact message: %s", e)
                error_message = "Sorry, there was an error submitting your message. Please try again."
    
    context = {
        'success_message': success_message,
        'error_message': error_message,
    }
    context.update(_seo_context(
        request,
        title="Contact Nexalix | IT & Innovation Consulting",
        description="Contact Nexalix Technologies to discuss your digital transformation, AI, cloud, and software delivery goals.",
    ))
    return render(request, "contact.html", context)


def send_admin_notification(contact_message):
    """Send email notification to admin about new contact message"""
    try:
        # Resolve recipients from settings and always include contact notification inbox.
        configured_recipients = getattr(settings, "ADMIN_EMAILS", [])
        if isinstance(configured_recipients, str):
            configured_recipients = [
                email.strip()
                for email in configured_recipients.split(",")
                if email.strip()
            ]

        admin_emails = list(configured_recipients)
        contact_notification_email = getattr(
            settings,
            "CONTACT_NOTIFICATION_EMAIL",
            "dachiek4@gmail.com",
        ).strip()

        if contact_notification_email and contact_notification_email not in admin_emails:
            admin_emails.append(contact_notification_email)

        if not admin_emails:
            admin_emails = ["dachiek4@gmail.com"]
        
        # Create email subject
        subject = f"📧 New Contact Form Submission: {contact_message.service or 'General Inquiry'}"
        
        # Get site URL for admin link
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        admin_url = f"{site_url}/admin/nexalix_app/contactmessage/{contact_message.id}/change/"
        
        # Create email content
        context = {
            'contact': contact_message,
            'admin_url': admin_url,
            'site_url': site_url,
        }
        
        # Plain text version
        message_text = f"""
NEW CONTACT FORM SUBMISSION

Name: {contact_message.full_name}
Email: {contact_message.email}
Service: {contact_message.service or 'Not specified'}
Time: {contact_message.submitted_at.strftime('%Y-%m-%d %H:%M:%S')}

Message:
{contact_message.message}

---
View in Admin: {admin_url}
Reply to: {contact_message.email}
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=message_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=False,
        )
        
        # Mark as notified after successful send
        contact_message.mark_admin_notified()
        return True
        
    except Exception as e:
        logger.exception("Error sending admin notification email: %s", e)
        return False


def send_user_confirmation(contact_message):
    """Send auto-reply confirmation to the user"""
    try:
        subject = "Thank you for contacting Nexalix Technologies"
        
        message = f"""
Dear {contact_message.full_name},

Thank you for reaching out to Nexalix Technologies!

We have received your message regarding "{contact_message.service or 'our services'}".

Our team will review your inquiry and get back to you within 24-48 hours.

For reference, here's a summary of your submission:
- Name: {contact_message.full_name}
- Email: {contact_message.email}
- Service: {contact_message.service or 'Not specified'}
- Submitted: {contact_message.submitted_at.strftime('%Y-%m-%d %H:%M')}

If you have any urgent questions, please don't hesitate to contact us directly.

Best regards,
The Nexalix Technologies Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[contact_message.email],
            fail_silently=True,  # Don't fail if user email fails
        )
        
        # Mark confirmation sent
        contact_message.mark_user_confirmation_sent()
        return True
        
    except Exception as e:
        logger.exception("Error sending user confirmation email: %s", e)
        return False

def web_dev(request):
    """Legacy web development service page"""
    try:
        service = Service.objects.get(slug='web-development', is_active=True)
        return service_detail(request, 'web-development')
    except Service.DoesNotExist:
        return render(request, 'services/web_dev.html')

def mobile_app(request):
    """Legacy mobile app development service page"""
    try:
        service = Service.objects.get(slug='mobile-app-development', is_active=True)
        return service_detail(request, 'mobile-app-development')
    except Service.DoesNotExist:
        return render(request, 'services/mobile_app.html')

def digital_marketing(request):
    """Legacy digital marketing service page"""
    try:
        service = Service.objects.get(slug='digital-marketing', is_active=True)
        return service_detail(request, 'digital-marketing')
    except Service.DoesNotExist:
        return render(request, 'services/digital_marketing.html')

def seo(request):
    """Legacy SEO service page"""
    try:
        service = Service.objects.get(slug='seo-optimization', is_active=True)
        return service_detail(request, 'seo-optimization')
    except Service.DoesNotExist:
        return render(request, 'services/seo.html')

def it_consult(request):
    """Legacy IT consulting service page"""
    try:
        service = Service.objects.get(slug='it-consulting', is_active=True)
        return service_detail(request, 'it-consulting')
    except Service.DoesNotExist:
        return render(request, 'services/it_consult.html')

def cloud(request):
    """Legacy cloud solutions service page"""
    try:
        service = Service.objects.get(slug='cloud-solutions', is_active=True)
        return service_detail(request, 'cloud-solutions')
    except Service.DoesNotExist:
        return render(request, 'services/cloud.html')

def syste_dev(request):
    """Legacy systems development service page"""
    try:
        service = Service.objects.get(slug='systems-development', is_active=True)
        return service_detail(request, 'systems-development')
    except Service.DoesNotExist:
        return render(request, 'services/syste_dev.html')

def ai_training(request):
    """Legacy AI training service page"""
    try:
        service = Service.objects.get(slug='ai-training', is_active=True)
        return service_detail(request, 'ai-training')
    except Service.DoesNotExist:
        return render(request, 'services/ai_training.html')


# ========================================
# CASE STUDIES VIEWS
# ========================================

def case_studies_list(request):
    """Display all case studies"""
    case_studies_all = list(CaseStudy.objects.filter(is_active=True).order_by('order'))

    case_schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Nexalix Case Studies",
        "itemListElement": [_case_study_schema(request, case, index + 1) for index, case in enumerate(case_studies_all)],
    }
    dynamic_description = (
        f"Explore {len(case_studies_all)} Nexalix case studies and success stories across digital transformation programs."
        if case_studies_all
        else "Explore Nexalix case studies and success stories across digital transformation programs."
    )

    context = {
        'case_studies': case_studies_all,
        'page_title': 'Case Studies - Success Stories',
        'meta_description': dynamic_description,
    }
    context.update(_seo_context(
        request,
        title="Case Studies | Nexalix Success Stories",
        description=dynamic_description,
        keywords=_build_keywords(
            [case.title for case in case_studies_all[:8]],
            [tag for case in case_studies_all[:8] for tag in case.get_tags_list()],
            "case studies",
            "client success stories",
        ),
        schemas=[case_schema],
    ))
    return render(request, 'case_studies.html', context)


def case_study_detail(request, slug):
    """Display single case study detail"""
    case_study = None
    for item in CaseStudy.objects.filter(is_active=True):
        if slugify(item.title) == slug:
            case_study = item
            break

    if not case_study:
        return redirect('case_studies')

    related_cases = CaseStudy.objects.filter(is_active=True).exclude(id=case_study.id).order_by('order')[:3]
    
    context = {
        'case_study': case_study,
        'related_cases': related_cases,
        'page_title': case_study.title,
        'meta_description': case_study.description[:160] if len(case_study.description) > 160 else case_study.description,
    }
    context.update(_seo_context(
        request,
        title=f"{case_study.title} | Nexalix Case Study",
        description=case_study.description,
        keywords=_build_keywords(case_study.title, case_study.get_tags_list(), "project implementation"),
        og_type="article",
        image_url=(case_study.image.url if case_study.image else ""),
        schemas=[{"@context": "https://schema.org", **_case_study_schema(request, case_study)}],
    ))
    return render(request, 'case_study_detail.html', context)
