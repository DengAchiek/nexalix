from django.core.cache import cache

HOME_CONTEXT_CACHE_KEY = "home_context_v2"
SEARCH_INDEX_CACHE_KEY = "site_search_index_v1"
SEARCH_INDEX_CACHE_TTL = 300
FOOTER_CONTEXT_CACHE_KEY = "global_site_footer_context_v1"
DASHBOARD_AGGREGATES_CACHE_PREFIX = "dashboard_aggregates_v2"
DASHBOARD_PERIODS = (7, 30, 90)


def get_dashboard_aggregate_cache_key(period_days):
    return f"{DASHBOARD_AGGREGATES_CACHE_PREFIX}:{period_days}"


def invalidate_home_cache():
    cache.delete(HOME_CONTEXT_CACHE_KEY)
    cache.delete(SEARCH_INDEX_CACHE_KEY)


def invalidate_footer_cache():
    cache.delete(FOOTER_CONTEXT_CACHE_KEY)


def invalidate_dashboard_cache():
    for period in DASHBOARD_PERIODS:
        cache.delete(get_dashboard_aggregate_cache_key(period))


def invalidate_all_view_caches():
    invalidate_home_cache()
    invalidate_footer_cache()
    invalidate_dashboard_cache()
