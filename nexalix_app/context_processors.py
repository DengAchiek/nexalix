from django.core.cache import cache
from django.urls import reverse
from django.utils.text import slugify

from .cache_utils import SEARCH_INDEX_CACHE_KEY, SEARCH_INDEX_CACHE_TTL
from .models import BlogPost, CaseStudy, Industry, Service


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

        for case in CaseStudy.objects.filter(is_active=True).order_by("order", "-created_at")[:24]:
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

    return {
        "global_search_index": search_index,
    }
