# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    HeroSection, Testimonial, AboutSection, ProcessStep,
    Industry, TechnologyCategory, Technology, CaseStudy, NewsletterSignup,
    Statistic, BlogPost, Partner, Award, ContactCTA,
    Service, ServiceFeature, ServiceTechnology, PricingPlan
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

# ========== SERVICE MODELS (ONE TIME ONLY) ==========
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