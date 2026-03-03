# admin.py
from django.contrib import admin
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils.html import format_html
from .models import (
    HeroSection, Testimonial, AboutSection, ProcessStep,
    Industry, TechnologyCategory, Technology, CaseStudy, NewsletterSignup,
    Statistic, BlogPost, Partner, Award, ContactCTA,
    Service, ServiceFeature, ServiceTechnology, PricingPlan, ContactMessage
)

# ========== EXISTING MODELS (NON-SERVICE) ==========
@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_at']
    list_editable = ['is_active']
    list_filter = ['is_active']

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'rating', 'is_active', 'created_at']
    list_filter = ['is_active', 'rating']
    search_fields = ['name', 'company', 'content']

@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active']

@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ['number', 'title', 'order']
    ordering = ['order']

@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    ordering = ['order']

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
    list_display = ['title', 'order', 'is_active', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']
    ordering = ['order']

@admin.register(NewsletterSignup)
class NewsletterSignupAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active']

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
    list_display = ['name', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    ordering = ['order']

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
    list_display = ['title', 'category', 'order', 'is_active', 'created_at', 'icon_preview']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'short_description', 'full_description']
    list_editable = ['order', 'is_active']
    prepopulated_fields = {'slug': ['title']}
    inlines = [ServiceFeatureInline, ServiceTechnologyInline, PricingPlanInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'short_description', 'full_description', 'category', 'order', 'is_active')
        }),
        ('Visuals', {
            'fields': ('icon', 'featured_image', 'icon_preview')
        }),
        ('Details', {
            'fields': ('key_features', 'technologies', 'pricing_info')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['icon_preview']
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html(f'<i class="{obj.icon} fa-2x"></i> <span>{obj.icon}</span>')
        return "-"
    icon_preview.short_description = 'Icon Preview'

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


