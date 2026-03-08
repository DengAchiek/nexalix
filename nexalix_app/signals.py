from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .cache_utils import invalidate_dashboard_cache, invalidate_home_cache
from .models import (
    AboutSection,
    Award,
    BlogPost,
    CaseStudy,
    ContactCTA,
    ContactMessage,
    HeroSection,
    Industry,
    NewsletterSignup,
    Partner,
    ProcessStep,
    QuoteRequest,
    Service,
    Statistic,
    Technology,
    TechnologyCategory,
    Testimonial,
)

HOME_CACHE_MODELS = (
    HeroSection,
    Service,
    Testimonial,
    AboutSection,
    ProcessStep,
    Industry,
    TechnologyCategory,
    Technology,
    CaseStudy,
    NewsletterSignup,
    Statistic,
    BlogPost,
    Partner,
    Award,
    ContactCTA,
)


@receiver(post_save, sender=ContactMessage)
@receiver(post_delete, sender=ContactMessage)
@receiver(post_save, sender=QuoteRequest)
@receiver(post_delete, sender=QuoteRequest)
def invalidate_dashboard_aggregates_on_submission_change(sender, **kwargs):
    invalidate_dashboard_cache()


def _invalidate_home_context_on_content_change(sender, **kwargs):
    invalidate_home_cache()


for model in HOME_CACHE_MODELS:
    post_save.connect(_invalidate_home_context_on_content_change, sender=model, weak=False)
    post_delete.connect(_invalidate_home_context_on_content_change, sender=model, weak=False)
