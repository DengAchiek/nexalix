from django.conf import settings
from django.core.cache import cache
from django.urls import reverse
from django.utils.text import slugify

from .cache_utils import FOOTER_CONTEXT_CACHE_KEY, SEARCH_INDEX_CACHE_KEY, SEARCH_INDEX_CACHE_TTL
from .models import BlogPost, CaseStudy, Industry, NewsletterSignup, Service, SolutionPage


def _search_entry(title, description, url, category, keywords=None):
    return {
        "title": title,
        "description": description,
        "url": url,
        "category": category,
        "keywords": keywords or [],
    }


def global_site_context(_request):
    search_index = cache.get(SEARCH_INDEX_CACHE_KEY)
    if search_index is None:
        search_index = [
            _search_entry("Home", "Company overview and featured solutions", reverse("home"), "Page"),
            _search_entry("About", "Vision, mission, and core values", reverse("about"), "Page"),
            _search_entry("Services", "Technology and consulting offerings", reverse("services"), "Page"),
            _search_entry("Auto Quote", "Generate a live project cost estimate", reverse("quote_generator"), "Page"),
            _search_entry("Industries", "Sector-focused transformation work", reverse("industries"), "Page"),
            _search_entry("How We Work", "Delivery process and methodology", reverse("how_we_work"), "Page"),
            _search_entry("Why Choose Us", "Differentiators and value proposition", reverse("why_choose_us"), "Page"),
            _search_entry("Contact", "Get proposal and consultation support", reverse("contact"), "Page"),
        ]

        for service in Service.objects.filter(is_active=True).order_by("order", "title")[:40]:
            keywords = service.get_technologies_list()[:6]
            service_url = reverse("service_detail", args=[service.slug]) if service.slug else reverse("services")
            search_index.append(
                _search_entry(
                    title=service.title,
                    description=(service.short_description or service.full_description or "")[:180],
                    url=service_url,
                    category="Service",
                    keywords=keywords,
                )
            )

        for page in SolutionPage.objects.filter(is_active=True).order_by("order", "nav_title")[:20]:
            search_index.append(
                _search_entry(
                    title=page.nav_title,
                    description=(page.subheadline or "")[:180],
                    url=reverse("solution_landing", args=[page.slug]),
                    category="Solution",
                    keywords=page.get_keywords_list()[:8],
                )
            )

        for industry in Industry.objects.filter(is_active=True).order_by("order", "name")[:24]:
            search_index.append(
                _search_entry(
                    title=industry.name,
                    description=(industry.description or "")[:180],
                    url=reverse("industries"),
                    category="Industry",
                    keywords=["industry", "sector", industry.name.lower()],
                )
            )

        for case in CaseStudy.objects.filter(is_active=True, is_published=True).order_by("order", "-created_at")[:24]:
            search_index.append(
                _search_entry(
                    title=case.title,
                    description=(case.description or "")[:180],
                    url=reverse("case_study_detail", args=[slugify(case.title)]),
                    category="Case Study",
                    keywords=case.get_tags_list()[:8],
                )
            )

        for post in BlogPost.objects.filter(is_published=True).order_by("-publish_date")[:20]:
            search_index.append(
                _search_entry(
                    title=post.title,
                    description=(post.excerpt or post.content or "")[:180],
                    url=reverse("home"),
                    category="Insights",
                    keywords=["blog", "insights", "thought leadership"],
                )
            )

        cache.set(SEARCH_INDEX_CACHE_KEY, search_index, SEARCH_INDEX_CACHE_TTL)

    footer_context = cache.get(FOOTER_CONTEXT_CACHE_KEY)
    if footer_context is None:
        footer_industries = list(Industry.objects.filter(is_active=True).order_by("order", "name")[:6])
        footer_newsletter = NewsletterSignup.objects.filter(is_active=True).first()
        configured_socials = [
            ("LinkedIn", "fab fa-linkedin-in", getattr(settings, "FOOTER_LINKEDIN_URL", "").strip()),
            ("Facebook", "fab fa-facebook-f", getattr(settings, "FOOTER_FACEBOOK_URL", "").strip()),
            ("Instagram", "fab fa-instagram", getattr(settings, "FOOTER_INSTAGRAM_URL", "").strip()),
            ("X", "fab fa-x-twitter", getattr(settings, "FOOTER_X_URL", "").strip()),
        ]
        footer_social_links = [
            {"label": label, "icon": icon, "url": url}
            for label, icon, url in configured_socials
            if url
        ]
        footer_context = {
            "footer_industries": footer_industries,
            "footer_newsletter": footer_newsletter,
            "footer_positioning": getattr(
                settings,
                "FOOTER_POSITIONING",
                "Consulting-led software, AI, data, and automation delivery for businesses scaling operations.",
            ),
            "footer_contact_email": getattr(settings, "CONTACT_EMAIL", "").strip() or getattr(settings, "CONTACT_NOTIFICATION_EMAIL", "").strip(),
            "footer_contact_phone": getattr(settings, "CONTACT_PHONE", "+254768774232").strip(),
            "footer_contact_phone_display": getattr(settings, "CONTACT_PHONE_DISPLAY", "+254 768 774 232").strip(),
            "footer_contact_location": getattr(settings, "CONTACT_LOCATION", "Kenya").strip(),
            "footer_whatsapp_url": getattr(settings, "CHATBOT_WHATSAPP_URL", "https://wa.me/254768774232").strip(),
            "footer_service_regions": getattr(
                settings,
                "FOOTER_SERVICE_REGIONS",
                "Kenya, East Africa, and remote global delivery",
            ).strip(),
            "footer_response_promise": getattr(
                settings,
                "FOOTER_RESPONSE_PROMISE",
                "Response within 24 hours",
            ).strip(),
            "footer_support_hours": getattr(
                settings,
                "FOOTER_SUPPORT_HOURS",
                "Business hours (EAT) with project-based support coverage",
            ).strip(),
            "footer_legal_name": getattr(
                settings,
                "COMPANY_LEGAL_NAME",
                "Nexalix Technologies Ltd.",
            ).strip(),
            "footer_social_links": footer_social_links,
        }
        cache.set(FOOTER_CONTEXT_CACHE_KEY, footer_context, 300)

    return {
        "global_search_index": search_index,
        **footer_context,
    }
