# admin.py
import logging

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.admin.sites import NotRegistered
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.html import format_html
from .models import (
    HeroSection, Testimonial, AboutSection, ProcessStep,
    Industry, TechnologyCategory, Technology, CaseStudy, NewsletterSignup,
    Statistic, BlogPost, Partner, Award, ContactCTA,
    Service, ServiceFeature, ServiceTechnology, PricingPlan, ContactMessage,
    ServiceSolutionCluster, SolutionPage,
    QuoteAddon, QuoteRequest, DashboardSavedFilter, ChatbotLead, UpdatesSubscriber
)

User = get_user_model()
logger = logging.getLogger(__name__)


def render_image_preview(image_field, label="Image preview"):
    if image_field:
        return format_html(
            '<div style="display:grid;gap:8px;"><img src="{}" alt="{}" style="max-width:220px;border-radius:14px;border:1px solid #d9e4f2;box-shadow:0 10px 24px rgba(17,39,78,.08);" /><span style="font-size:12px;color:#5b718b;">{}</span></div>',
            image_field.url,
            label,
            label,
        )
    return format_html('<span style="color:#8aa0bc;">No image uploaded yet.</span>')

# ========== EXISTING MODELS (NON-SERVICE) ==========
@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_at']
    list_editable = ['is_active']
    list_filter = ['is_active']

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'position', 'review_source', 'rating', 'sort_order', 'is_active', 'is_published', 'created_at']
    list_editable = ['sort_order', 'is_active', 'is_published']
    list_filter = ['is_active', 'is_published', 'rating']
    search_fields = ['name', 'company', 'position', 'content', 'review_source']
    ordering = ['sort_order', '-created_at']
    readonly_fields = ['avatar_preview']
    fieldsets = (
        ('Profile', {
            'fields': ('name', 'position', 'company', 'review_source', 'rating', 'avatar', 'avatar_preview')
        }),
        ('Review', {
            'fields': ('content',)
        }),
        ('Publishing', {
            'fields': ('sort_order', 'is_active', 'is_published')
        }),
    )

    def avatar_preview(self, obj):
        return render_image_preview(obj.avatar, "Avatar preview")
    avatar_preview.short_description = "Avatar preview"

@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active']

@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ['number', 'title', 'icon', 'order']
    ordering = ['order']
    search_fields = ['number', 'title', 'description', 'outputs']


@admin.register(ServiceSolutionCluster)
class ServiceSolutionClusterAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'order', 'is_active', 'show_on_homepage']
    list_editable = ['order', 'is_active', 'show_on_homepage']
    search_fields = ['title', 'slug', 'value_statement', 'business_problem', 'who_for', 'keywords']
    ordering = ['order', 'title']


@admin.register(SolutionPage)
class SolutionPageAdmin(admin.ModelAdmin):
    list_display = ['nav_title', 'slug', 'solution_cluster', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['nav_title', 'slug', 'headline', 'subheadline', 'keywords']
    list_filter = ['solution_cluster', 'is_active']
    ordering = ['order', 'nav_title']
    readonly_fields = ['social_share_preview']
    fieldsets = (
        ('Content', {
            'fields': ('nav_title', 'slug', 'headline', 'subheadline', 'solution_cluster', 'order', 'is_active')
        }),
        ('Structured Content', {
            'fields': ('problems', 'deliverables', 'technologies', 'keywords', 'faq_items')
        }),
        ('Visuals', {
            'fields': ('social_share_image', 'social_share_preview')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'canonical_url', 'schema_markup_json'),
            'classes': ('collapse',)
        }),
    )

    def social_share_preview(self, obj):
        return render_image_preview(obj.social_share_image, "Solution image preview")
    social_share_preview.short_description = "Solution image preview"

@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active', 'image_preview']
    list_editable = ['order', 'is_active']
    ordering = ['order']
    readonly_fields = ['image_preview']
    fieldsets = (
        ('Content', {
            'fields': ('name', 'description', 'icon', 'image', 'image_preview')
        }),
        ('Publishing', {
            'fields': ('order', 'is_active')
        }),
    )

    def image_preview(self, obj):
        return render_image_preview(obj.image, "Industry image preview")
    image_preview.short_description = "Industry image preview"

class TechnologyInline(admin.TabularInline):
    model = Technology
    extra = 1

@admin.register(TechnologyCategory)
class TechnologyCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order']
    list_editable = ['order']
    inlines = [TechnologyInline]
    ordering = ['order']

@admin.register(CaseStudy)
class CaseStudyAdmin(admin.ModelAdmin):
    list_display = ['title', 'client_name', 'industry', 'proof_type', 'is_featured', 'is_active', 'is_published', 'order', 'created_at']
    list_editable = ['is_featured', 'is_active', 'is_published', 'order']
    list_filter = ['industry', 'proof_type', 'is_featured', 'is_active', 'is_published']
    search_fields = ['title', 'client_name', 'description', 'challenge', 'solution', 'results', 'tags', 'tech_stack']
    ordering = ['-is_featured', 'order', '-created_at']
    readonly_fields = ['image_preview', 'social_share_preview']
    fieldsets = (
        ('Core Story', {
            'fields': ('title', 'client_name', 'industry', 'proof_type', 'description', 'image', 'image_preview')
        }),
        ('Delivery Details', {
            'fields': ('challenge', 'solution', 'results', 'tech_stack', 'tags', 'engagement_type', 'link')
        }),
        ('Social Share Visual', {
            'fields': ('social_share_image', 'social_share_preview')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'canonical_url', 'schema_markup_json'),
            'classes': ('collapse',)
        }),
        ('Publishing', {
            'fields': ('is_featured', 'is_active', 'is_published', 'order')
        }),
    )

    def image_preview(self, obj):
        return render_image_preview(obj.image, "Case study image preview")
    image_preview.short_description = "Case study image preview"

    def social_share_preview(self, obj):
        return render_image_preview(obj.social_share_image, "Social share image preview")
    social_share_preview.short_description = "Social share image preview"

@admin.register(NewsletterSignup)
class NewsletterSignupAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active']


@admin.register(UpdatesSubscriber)
class UpdatesSubscriberAdmin(admin.ModelAdmin):
    list_display = ["email", "source", "is_active", "created_at"]
    list_filter = ["source", "is_active", "created_at"]
    search_fields = ["email"]
    ordering = ["-created_at"]

@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ['name', 'value', 'suffix', 'order', 'is_active']
    list_editable = ['value', 'suffix', 'order', 'is_active']
    ordering = ['order']

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'publish_date', 'is_published']
    list_filter = ['is_published', 'publish_date']
    search_fields = ['title', 'excerpt', 'content']
    prepopulated_fields = {'slug': ['title']}

@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'website', 'order', 'is_active', 'is_published', 'logo_preview']
    list_editable = ['order', 'is_active', 'is_published']
    list_filter = ['industry', 'is_active', 'is_published']
    search_fields = ['name', 'industry', 'description', 'website']
    ordering = ['order', 'name']
    readonly_fields = ['logo_preview']
    fieldsets = (
        ('Partner', {
            'fields': ('name', 'industry', 'description', 'website', 'logo', 'logo_preview')
        }),
        ('Publishing', {
            'fields': ('order', 'is_active', 'is_published')
        }),
    )

    def logo_preview(self, obj):
        return render_image_preview(obj.logo, "Partner logo preview")
    logo_preview.short_description = "Partner logo preview"

@admin.register(Award)
class AwardAdmin(admin.ModelAdmin):
    list_display = ['name', 'year', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['year', 'is_active']
    ordering = ['-year', 'order']

@admin.register(ContactCTA)
class ContactCTAAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active']


class ServiceFeatureInline(admin.TabularInline):
    model = ServiceFeature
    extra = 1

class ServiceTechnologyInline(admin.TabularInline):
    model = ServiceTechnology
    extra = 1

class PricingPlanInline(admin.TabularInline):
    model = PricingPlan
    extra = 1

# ONLY ONE ServiceAdmin class - this is the correct one with all features
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'quote_base_price', 'order', 'is_active', 'created_at', 'icon_preview']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'short_description', 'full_description']
    list_editable = ['order', 'is_active']
    prepopulated_fields = {'slug': ['title']}
    inlines = [ServiceFeatureInline, ServiceTechnologyInline, PricingPlanInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'short_description', 'full_description', 'category', 'solution_cluster', 'order', 'is_active')
        }),
        ('Visuals', {
            'fields': ('icon', 'featured_image', 'featured_image_preview', 'icon_preview')
        }),
        ('Details', {
            'fields': (
                'key_features',
                'technologies',
                'faq_items',
                'pricing_info',
                'quote_base_price',
                'quote_delivery_weeks',
                'show_in_quote_generator',
            )
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'canonical_url', 'social_share_image', 'social_share_preview', 'schema_markup_json'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['icon_preview', 'featured_image_preview', 'social_share_preview']
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html(f'<i class="{obj.icon} fa-2x"></i> <span>{obj.icon}</span>')
        return "-"
    icon_preview.short_description = 'Icon Preview'

    def featured_image_preview(self, obj):
        return render_image_preview(obj.featured_image, "Service image preview")
    featured_image_preview.short_description = "Service image preview"

    def social_share_preview(self, obj):
        return render_image_preview(obj.social_share_image, "Social share image preview")
    social_share_preview.short_description = "Social share image preview"

@admin.register(ServiceFeature)
class ServiceFeatureAdmin(admin.ModelAdmin):
    list_display = ['title', 'service', 'order']
    list_filter = ['service']
    search_fields = ['title', 'description']
    list_editable = ['order']

@admin.register(ServiceTechnology)
class ServiceTechnologyAdmin(admin.ModelAdmin):
    list_display = ['name', 'service', 'icon']
    list_filter = ['service']
    search_fields = ['name', 'description']

@admin.register(PricingPlan)
class PricingPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'service', 'price', 'period', 'is_popular', 'order']
    list_filter = ['service', 'is_popular']
    list_editable = ['price', 'period', 'is_popular', 'order']
    search_fields = ['name', 'features']


@admin.register(QuoteAddon)
class QuoteAddonAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "order", "is_active"]
    list_editable = ["price", "order", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "description"]
    ordering = ["order", "name"]


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = [
        "quote_reference",
        "full_name",
        "email",
        "service",
        "estimated_total",
        "currency",
        "status",
        "created_at",
    ]
    list_filter = ["status", "service", "complexity", "timeline", "support_plan", "created_at"]
    search_fields = ["quote_reference", "full_name", "email", "company", "project_summary"]
    readonly_fields = [
        "quote_reference",
        "estimated_subtotal",
        "addons_total",
        "support_total",
        "estimated_total",
        "estimated_min",
        "estimated_max",
        "estimated_weeks",
        "created_at",
    ]
    filter_horizontal = ["selected_addons"]
    fieldsets = (
        ("Request Info", {
            "fields": (
                "quote_reference",
                "full_name",
                "email",
                "company",
                "phone",
                "service",
                "project_summary",
                "status",
                "admin_notes",
                "created_at",
            )
        }),
        ("Configuration", {
            "fields": ("complexity", "timeline", "support_plan", "selected_addons")
        }),
        ("Estimated Breakdown", {
            "fields": (
                "currency",
                "estimated_subtotal",
                "addons_total",
                "support_total",
                "estimated_total",
                "estimated_min",
                "estimated_max",
                "estimated_weeks",
            )
        }),
    )


def send_admin_notification(contact_message):
    try:
        admin_emails = getattr(settings, 'ADMIN_EMAILS', [settings.DEFAULT_FROM_EMAIL])

        subject = f"New Contact Form Submission: {contact_message.service or 'General Inquiry'}"

        body = f"""
Name: {contact_message.full_name}
Email: {contact_message.email}
Service: {contact_message.service or 'Not specified'}

Message:
{contact_message.message}
        """

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=admin_emails,
            reply_to=[contact_message.email],
        )

        email.send(fail_silently=False)  # 🚀 REAL-TIME SEND

        contact_message.mark_admin_notified()
        return True

    except Exception as e:
        print("ADMIN EMAIL ERROR:", e)
        return False

def send_user_confirmation(contact_message):
    try:
        subject = "We’ve received your message – Nexalix Technologies"

        body = f"""
Hi {contact_message.full_name},

Thanks for contacting Nexalix Technologies.

We’ve received your message and will respond within 24–48 hours.

Summary:
Service: {contact_message.service or 'General'}
Message:
{contact_message.message}

Regards,
Nexalix Team
        """

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[contact_message.email],
        )

        email.send(fail_silently=False)  

        contact_message.mark_user_confirmation_sent()
        return True

    except Exception as e:
        print("USER EMAIL ERROR:", e)
        return False


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'service', 'submitted_at', 'is_read', 'admin_notified')
    list_filter = ('is_read', 'admin_notified', 'submitted_at', 'service')
    search_fields = ('full_name', 'email', 'message')
    readonly_fields = ('submitted_at', 'admin_notified_at', 'user_confirmation_sent_at')
    list_per_page = 20
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('full_name', 'email', 'service')
        }),
        ('Message', {
            'fields': ('message',)
        }),
        ('Status', {
            'fields': ('is_read', 'admin_notified', 'admin_notified_at', 
                      'user_confirmation_sent', 'user_confirmation_sent_at')
        }),
        ('Timestamps', {
            'fields': ('submitted_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_unread', 'resend_admin_notification']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
    mark_as_unread.short_description = "Mark selected messages as unread"
    
    def resend_admin_notification(self, request, queryset):
        from .views import send_admin_notification
        count = 0
        for message in queryset:
            if send_admin_notification(message):
                count += 1
        self.message_user(request, f"Resent notifications for {count} messages.")
    resend_admin_notification.short_description = "Resend admin notification email"


@admin.register(DashboardSavedFilter)
class DashboardSavedFilterAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "period_days", "role_view", "activity_filter", "updated_at")
    list_filter = ("role_view", "activity_filter", "period_days")
    search_fields = ("name", "user__username", "search_query")


@admin.register(ChatbotLead)
class ChatbotLeadAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "company",
        "lead_status",
        "is_escalated",
        "escalation_channel",
        "created_at",
    )
    list_filter = ("lead_status", "is_escalated", "escalation_channel", "created_at")
    search_fields = ("full_name", "email", "phone", "company", "project_needs", "interested_services")
    readonly_fields = ("session_key", "created_at", "updated_at")


def send_staff_access_granted_email(user):
    recipient = (user.email or "").strip()
    if not recipient:
        return False, "missing_email"

    site_url = getattr(settings, "SITE_URL", "http://localhost:8000").rstrip("/")
    login_url = f"{site_url}/admin/login/"
    first_name = (user.first_name or user.username or "there").strip()

    subject = "Your Nexalix admin access is ready"
    body = f"""
Hi {first_name},

Your Nexalix account has been approved for staff access.

You can now sign in to the admin area here:
{login_url}

Username: {user.username}

If you did not request this access, please contact the Nexalix team immediately.

Regards,
Nexalix Technologies
    """.strip()

    try:
        email = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        email.send(fail_silently=False)
        return True, ""
    except Exception as exc:
        logger.exception("Failed to send staff approval email for user %s: %s", user.pk, exc)
        return False, "send_failed"


@admin.action(description="Approve staff access for selected users")
def approve_staff_access(modeladmin, request, queryset):
    pending_users = list(queryset.exclude(is_staff=True))
    approved_count = 0
    emailed_count = 0
    missing_email_count = 0
    failed_email_count = 0

    for user in pending_users:
        user.is_staff = True
        user.save(update_fields=["is_staff"])
        approved_count += 1

        sent, reason = send_staff_access_granted_email(user)
        if sent:
            emailed_count += 1
        elif reason == "missing_email":
            missing_email_count += 1
        else:
            failed_email_count += 1

    modeladmin.message_user(
        request,
        f"Granted staff access to {approved_count} user(s). Approval email sent to {emailed_count}.",
        level=messages.SUCCESS,
    )
    if missing_email_count or failed_email_count:
        modeladmin.message_user(
            request,
            (
                f"{missing_email_count} user(s) had no email address and "
                f"{failed_email_count} approval email(s) could not be delivered."
            ),
            level=messages.WARNING,
        )


@admin.action(description="Remove staff access for selected users")
def remove_staff_access(modeladmin, request, queryset):
    updated = queryset.filter(is_staff=True, is_superuser=False).update(is_staff=False)
    modeladmin.message_user(
        request,
        f"Removed staff access from {updated} user(s). Superusers were left unchanged.",
    )


class NexalixUserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_superuser", "date_joined")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("username", "first_name", "last_name", "email")
    ordering = ("-date_joined",)
    actions = [approve_staff_access, remove_staff_access]

    def save_model(self, request, obj, form, change):
        should_send_approval_email = False
        if change:
            original = User.objects.filter(pk=obj.pk).only("is_staff").first()
            should_send_approval_email = bool(original and not original.is_staff and obj.is_staff)

        super().save_model(request, obj, form, change)

        if not should_send_approval_email:
            return

        sent, reason = send_staff_access_granted_email(obj)
        if sent:
            self.message_user(
                request,
                f"Approval email sent to {obj.email}.",
                level=messages.SUCCESS,
            )
        elif reason == "missing_email":
            self.message_user(
                request,
                "Staff access was granted, but the user does not have an email address to notify.",
                level=messages.WARNING,
            )
        else:
            self.message_user(
                request,
                "Staff access was granted, but the approval email could not be sent.",
                level=messages.WARNING,
            )


try:
    admin.site.unregister(User)
except NotRegistered:
    pass

admin.site.register(User, NexalixUserAdmin)
