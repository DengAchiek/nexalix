from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.urls import reverse
from urllib.parse import urlencode
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
import math
from .models import (
    HeroSection, Service, Testimonial, AboutSection, ProcessStep,
    Industry, TechnologyCategory, CaseStudy, NewsletterSignup,
    Statistic, BlogPost, Partner, Award, ContactCTA,
    ServiceFeature, ServiceTechnology, PricingPlan, ContactMessage,
    QuoteAddon, QuoteRequest
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


def _money(value):
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


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
    # Get active hero section
    hero = HeroSection.objects.filter(is_active=True).first()
    
    # Get featured services
    services = Service.objects.filter(is_featured=True).order_by('order')[:3]
    
    # Get testimonials
    testimonials = Testimonial.objects.filter(is_active=True).order_by('-created_at')[:2]
    
    # Get about section
    about = AboutSection.objects.filter(is_active=True).first()
    
    # Get process steps
    process_steps = ProcessStep.objects.all().order_by('order')
    
    # Get industries
    industries = Industry.objects.filter(is_active=True).order_by('order')[:4]
    
    # Get technology categories with their technologies
    technology_categories = TechnologyCategory.objects.prefetch_related('technologies').all()
    
    # Get case studies for home page
    case_studies = CaseStudy.objects.filter(is_active=True).order_by('order')[:2]
    completed_projects = CaseStudy.objects.filter(is_active=True).order_by('-created_at', 'order')[:6]
    completed_projects_count = CaseStudy.objects.filter(is_active=True).count()
    
    # Get newsletter section
    newsletter = NewsletterSignup.objects.filter(is_active=True).first()
    
    # Get statistics
    statistics = Statistic.objects.filter(is_active=True).order_by('order')[:4]
    
    # Get blog posts
    blog_posts = BlogPost.objects.filter(is_published=True).order_by('-publish_date')[:2]
    
    # Get partners
    partners = Partner.objects.filter(is_active=True).order_by('order')
    
    # Get awards
    awards = Award.objects.filter(is_active=True).order_by('-year', 'order')[:3]
    
    # Get contact CTA
    contact_cta = ContactCTA.objects.filter(is_active=True).first()
    
    context = {
        'hero': hero,
        'services': services,
        'testimonials': testimonials,
        'about': about,
        'process_steps': process_steps,
        'industries': industries,
        'technology_categories': technology_categories,
        'case_studies': case_studies,
        'completed_projects': completed_projects,
        'completed_projects_count': completed_projects_count,
        'newsletter': newsletter,
        'statistics': statistics,
        'blog_posts': blog_posts,
        'partners': partners,
        'awards': awards,
        'contact_cta': contact_cta,
    }
    
    return render(request, "home.html", context)

def about(request):
    """About page view"""
    about_sections = AboutSection.objects.filter(is_active=True)
    primary_about = about_sections.first()
    context = {
        "about_sections": about_sections,
        "primary_about": primary_about,
    }
    return render(request, "about.html", context)

def services(request):
    """Services list page view"""
    # Get all active services, ordered by order field
    services_list = Service.objects.filter(is_active=True).order_by('order')
    
    # Group services by category
    services_by_category = {}
    for service in services_list:
        category = service.get_category_display()
        if category not in services_by_category:
            services_by_category[category] = []
        services_by_category[category].append(service)
    
    
    pricing_plans = PricingPlan.objects.all().order_by('order')
    
    context = {
        'services': services_list,
        'services_by_category': services_by_category,
        'pricing_plans': pricing_plans,  # This will work now
        'page_title': 'Our Services',
        'meta_description': 'Explore our comprehensive range of technology services including web development, mobile apps, digital marketing, and more.',
    }
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
    return render(request, 'service_detail.html', context)  # Changed from 'services/detail.html'

def industries(request):
    """Industries page view"""
    industries_list = Industry.objects.filter(is_active=True).order_by('order')
    return render(request, 'industries.html', {"industries": industries_list})

def how_we_work(request):
    """How We Work page view"""
    steps = ProcessStep.objects.all().order_by('order')
    return render(request, 'how_we_work.html', {"process_steps": steps})

def why_choose_us(request):
    """Why Choose Us page view"""
    return render(request, 'why_choose_us.html')


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

    if request.method == "POST" and request.POST.get("action") == "update_profile":
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

        query_params = {"period": str(period_days)}
        if search_query:
            query_params["q"] = search_query
        if activity_filter != "all":
            query_params["activity"] = activity_filter
        return redirect(f"{reverse('activity_dashboard')}?{urlencode(query_params)}")

    now = timezone.now()
    window_start = now - timedelta(days=period_days)

    contacts_queryset = ContactMessage.objects.all()
    quotes_queryset = QuoteRequest.objects.select_related("service")

    recent_contacts_all = contacts_queryset.filter(submitted_at__gte=window_start)
    recent_quotes_all = quotes_queryset.filter(created_at__gte=window_start)

    kpis = {
        "contacts_total": contacts_queryset.count(),
        "contacts_unread": contacts_queryset.filter(is_read=False).count(),
        "contacts_window": recent_contacts_all.count(),
        "quotes_total": quotes_queryset.count(),
        "quotes_new": quotes_queryset.filter(status="new").count(),
        "quotes_window": recent_quotes_all.count(),
    }

    filtered_contacts = recent_contacts_all
    filtered_quotes = recent_quotes_all
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

    contacts_daily_raw = filtered_contacts.annotate(day=TruncDate("submitted_at")).values("day").annotate(total=Count("id"))
    quotes_daily_raw = filtered_quotes.annotate(day=TruncDate("created_at")).values("day").annotate(total=Count("id"))
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
            "contacts": contact_count,
            "quotes": quote_count,
            "contacts_height": max(6, int((contact_count / max_count) * 120)) if contact_count else 4,
            "quotes_height": max(6, int((quote_count / max_count) * 120)) if quote_count else 4,
        })

    client_activities = []
    for message in filtered_contacts.order_by("-submitted_at")[:50]:
        client_activities.append({
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
        client_activities.append({
            "type": "quote",
            "title": f"Quote request {quote.quote_reference}",
            "subtitle": quote.service.title if quote.service else "Service not selected",
            "detail": quote.email,
            "timestamp": quote.created_at,
            "status": quote.get_status_display(),
            "admin_url": reverse("admin:nexalix_app_quoterequest_change", args=[quote.id]),
            "search_text": f"{quote.quote_reference} {quote.full_name} {quote.email} {quote.company or ''} {quote.project_summary}".lower(),
        })

    client_activities.sort(key=lambda item: item["timestamp"], reverse=True)
    if activity_filter in {"contact", "quote"}:
        client_activities = [item for item in client_activities if item["type"] == activity_filter]
    client_activities = client_activities[:60]

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
    logs_queryset = LogEntry.objects.select_related("user", "content_type").order_by("-action_time")
    if search_query:
        logs_queryset = logs_queryset.filter(
            Q(object_repr__icontains=search_query)
            | Q(user__username__icontains=search_query)
            | Q(change_message__icontains=search_query)
            | Q(content_type__model__icontains=search_query)
        )

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

    return render(request, "admin/activity_dashboard.html", {
        "kpis": kpis,
        "period_days": period_days,
        "client_activities": client_activities,
        "admin_logs": admin_logs,
        "trend_data": trend_data,
        "search_query": search_query,
        "activity_filter": activity_filter,
    })


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

    return render(request, "quote_generator.html", {
        "quote_services": quote_services,
        "quote_addons": quote_addons,
        "complexity_options": complexity_options,
        "timeline_options": timeline_options,
        "support_options": support_options,
        "success_message": success_message,
        "error_message": error_message,
        "generated_quote": generated_quote,
        "form_data": form_data,
    })


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
        print(f"Error sending quote notifications: {exc}")



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
        if not all([full_name, email, message]):
            error_message = "Please fill in all required fields (Name, Email, and Message)."
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
                print(f"Error saving contact: {e}")
                error_message = "Sorry, there was an error submitting your message. Please try again."
    
    return render(request, "contact.html", {
        'success_message': success_message,
        'error_message': error_message,
    })


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
        print(f"Error sending admin notification: {e}")
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
        print(f"Error sending user confirmation: {e}")
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
    case_studies_all = CaseStudy.objects.filter(is_active=True).order_by('order')

    context = {
        'case_studies': case_studies_all,
        'page_title': 'Case Studies - Success Stories',
        'meta_description': 'Explore our portfolio of successful projects and client success stories.',
    }
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
    return render(request, 'case_study_detail.html', context)
