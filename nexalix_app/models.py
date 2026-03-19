# nexalix_app/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
import uuid



class HeroSection(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.TextField()
    video = models.FileField(upload_to='videos/', null=True, blank=True)
    video_poster = models.ImageField(upload_to='images/', null=True, blank=True)
    button_text = models.CharField(max_length=50, default='Explore Our Services')
    button_link = models.CharField(max_length=200, default='services')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)  
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Service(models.Model):
    SERVICE_CATEGORIES = [
        ('development', 'Development'),
        ('marketing', 'Marketing'),
        ('cloud', 'Cloud & Infrastructure'),
        ('consulting', 'Consulting'),
        ('ai', 'Artificial Intelligence'),
        ('training', 'Training'),
    ]
    
    title = models.CharField(max_length=200)
    short_description = models.TextField(max_length=300)
    full_description = models.TextField()
    icon = models.CharField(
        max_length=100, 
        help_text="Font Awesome icon class, e.g., 'fas fa-code'",
        blank=True  # Added blank=True to match the first definition
    )
    category = models.CharField(max_length=50, choices=SERVICE_CATEGORIES, default='development')
    featured_image = models.ImageField(upload_to='services/', blank=True, null=True)
    order = models.IntegerField(default=0, help_text="Display order on services page")
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(
        default=False, 
        help_text="Show on homepage"
    )
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # SEO Fields
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    canonical_url = models.URLField(blank=True)
    social_share_image = models.ImageField(upload_to='seo/', blank=True, null=True)
    schema_markup_json = models.TextField(blank=True, help_text="Optional JSON-LD override or supplemental schema.")
    faq_items = models.TextField(
        blank=True,
        help_text="One FAQ per line using the format: Question | Answer"
    )
    
    # Additional features
    key_features = models.TextField(blank=True, help_text="One feature per line")
    technologies = models.TextField(blank=True, help_text="Technologies used (comma-separated)")
    pricing_info = models.TextField(blank=True, help_text="Pricing information")
    quote_base_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=3500.00,
        help_text="Base starting price used by the Auto Quote Generator."
    )
    quote_delivery_weeks = models.PositiveIntegerField(
        default=8,
        help_text="Typical delivery timeline in weeks for this service."
    )
    show_in_quote_generator = models.BooleanField(
        default=True,
        help_text="Make this service selectable in the Auto Quote Generator."
    )
    
    class Meta:
        ordering = ['order', 'title']
        verbose_name = "Service"
        verbose_name_plural = "Services"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def get_key_features_list(self):
        if self.key_features:
            return [feature.strip() for feature in self.key_features.split('\n') if feature.strip()]
        return []
    
    def get_technologies_list(self):
        if self.technologies:
            return [tech.strip() for tech in self.technologies.split(',') if tech.strip()]
        return []

    def get_faq_items_list(self):
        faqs = []
        for line in (self.faq_items or "").splitlines():
            if "|" not in line:
                continue
            question, answer = line.split("|", 1)
            question = question.strip()
            answer = answer.strip()
            if question and answer:
                faqs.append({"question": question, "answer": answer})
        return faqs
    
    def __str__(self):
        return self.title


class ServiceFeature(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='features')
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=100, blank=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.service.title} - {self.title}"


class ServiceTechnology(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='service_technologies')
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.service.title} - {self.name}"


class PricingPlan(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='pricing_plans')
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    period = models.CharField(max_length=50, default='month', help_text="e.g., month, year, project")
    features = models.TextField(help_text="One feature per line")
    is_popular = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def get_features_list(self):
        return [feature.strip() for feature in self.features.split('\n') if feature.strip()]
    
    def __str__(self):
        return f"{self.service.title} - {self.name}"


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    content = models.TextField()
    review_source = models.CharField(max_length=120, blank=True)
    avatar = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return f"{self.name} - {self.company}"


class AboutSection(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    button_text = models.CharField(max_length=50, default='Read More')
    button_link = models.CharField(max_length=200, default='about')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class ProcessStep(models.Model):
    number = models.CharField(max_length=10)
    title = models.CharField(max_length=100)
    description = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.number}. {self.title}"


class Industry(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = "Industries"

    def __str__(self):
        return self.name


class TechnologyCategory(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name_plural = "Technology Categories"

    def __str__(self):
        return self.name


class Technology(models.Model):
    category = models.ForeignKey(TechnologyCategory, on_delete=models.CASCADE, related_name='technologies')
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class CaseStudy(models.Model):
    PROOF_TYPE_CHOICES = [
        ("case_study", "Case Study"),
        ("sample_implementation", "Sample Implementation"),
        ("internal_prototype", "Internal Prototype"),
        ("solution_example", "Solution Example"),
    ]

    title = models.CharField(max_length=200)
    client_name = models.CharField(max_length=200, blank=True)
    industry = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    image = models.ImageField(upload_to='case_studies/')
    challenge = models.TextField(blank=True)
    solution = models.TextField(blank=True)
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated tags, e.g. Fintech, AI, Automation"
    )
    tech_stack = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated technologies used in this delivery story"
    )
    engagement_type = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional delivery tier or engagement type, e.g. MVP Sprint, Advisory Engagement"
    )
    results = models.TextField(blank=True)
    link = models.URLField(blank=True)
    proof_type = models.CharField(max_length=32, choices=PROOF_TYPE_CHOICES, default="case_study")
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(blank=True)
    canonical_url = models.URLField(blank=True)
    social_share_image = models.ImageField(upload_to='seo/', blank=True, null=True)
    schema_markup_json = models.TextField(blank=True, help_text="Optional JSON-LD override or supplemental schema.")
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', 'order', '-created_at']
        verbose_name_plural = "Case Studies"

    def __str__(self):
        return self.title

    def get_tags_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    def get_tech_stack_list(self):
        if self.tech_stack:
            return [tech.strip() for tech in self.tech_stack.split(",") if tech.strip()]
        return []


class NewsletterSignup(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.TextField()
    privacy_note = models.TextField(default="We respect your privacy. Unsubscribe at any time.")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Statistic(models.Model):
    name = models.CharField(max_length=100)
    value = models.IntegerField()
    suffix = models.CharField(max_length=10, blank=True, default='')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.name}: {self.value}{self.suffix}"


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    excerpt = models.TextField()
    content = models.TextField()
    image = models.ImageField(upload_to='blog/', blank=True, null=True)
    publish_date = models.DateField()
    is_published = models.BooleanField(default=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        ordering = ['-publish_date']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class QuoteAddon(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class QuoteRequest(models.Model):
    COMPLEXITY_CHOICES = [
        ("starter", "Starter / MVP"),
        ("growth", "Growth"),
        ("advanced", "Advanced"),
        ("enterprise", "Enterprise"),
    ]

    TIMELINE_CHOICES = [
        ("standard", "Standard Timeline"),
        ("accelerated", "Accelerated Timeline"),
        ("urgent", "Urgent Timeline"),
    ]

    SUPPORT_CHOICES = [
        ("none", "No Ongoing Support"),
        ("standard", "Standard Support"),
        ("premium", "Premium Support"),
    ]

    STATUS_CHOICES = [
        ("new", "New"),
        ("reviewed", "Reviewed"),
        ("sent", "Quote Sent"),
        ("won", "Won"),
        ("lost", "Lost"),
    ]

    quote_reference = models.CharField(max_length=32, unique=True, blank=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    company = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    service = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    complexity = models.CharField(max_length=20, choices=COMPLEXITY_CHOICES, default="growth")
    timeline = models.CharField(max_length=20, choices=TIMELINE_CHOICES, default="standard")
    support_plan = models.CharField(max_length=20, choices=SUPPORT_CHOICES, default="none")
    selected_addons = models.ManyToManyField(QuoteAddon, blank=True, related_name="quote_requests")
    project_summary = models.TextField()
    currency = models.CharField(max_length=8, default="USD")
    estimated_subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    addons_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    support_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    estimated_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    estimated_min = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    estimated_max = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    estimated_weeks = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new", db_index=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.quote_reference:
            self.quote_reference = self.generate_quote_reference()
        super().save(*args, **kwargs)

    def generate_quote_reference(self):
        return f"NQ-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    def __str__(self):
        return f"{self.quote_reference} - {self.full_name}"


class Partner(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(
        blank=True,
        help_text="Brief description shown on the homepage partner card"
    )
    industry = models.CharField(max_length=100, blank=True)
    logo = models.ImageField(upload_to='partners/', blank=True, null=True)
    website = models.URLField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Award(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='🏆')
    year = models.IntegerField()
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-year', 'order']

    def __str__(self):
        return f"{self.name} ({self.year})"


class ContactCTA(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    button_text = models.CharField(max_length=50, default='Contact Us')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title
    

class ContactMessage(models.Model):
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    service = models.CharField(max_length=100, blank=True)
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False, db_index=True)
    admin_notified = models.BooleanField(default=False)
    admin_notified_at = models.DateTimeField(null=True, blank=True)
    user_confirmation_sent = models.BooleanField(default=False)
    user_confirmation_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
    
    def __str__(self):
        return f"{self.full_name} - {self.email}"
    
    def mark_admin_notified(self):
        from django.utils import timezone
        self.admin_notified = True
        self.admin_notified_at = timezone.now()
        self.save()
    
    def mark_user_confirmation_sent(self):
        from django.utils import timezone
        self.user_confirmation_sent = True
        self.user_confirmation_sent_at = timezone.now()
        self.save()


class ChatbotLead(models.Model):
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("qualified", "Qualified"),
        ("closed", "Closed"),
    ]

    ESCALATION_CHOICES = [
        ("none", "None"),
        ("whatsapp", "WhatsApp"),
        ("contact", "Contact Form"),
        ("email", "Email"),
    ]

    session_key = models.CharField(max_length=64, db_index=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=200, blank=True)
    project_needs = models.TextField()
    interested_services = models.CharField(max_length=250, blank=True, help_text="Comma-separated service names.")
    assistant_summary = models.TextField(blank=True)
    source_page = models.CharField(max_length=255, blank=True)
    lead_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new", db_index=True)
    escalation_channel = models.CharField(max_length=20, choices=ESCALATION_CHOICES, default="none")
    is_escalated = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Chatbot Lead"
        verbose_name_plural = "Chatbot Leads"

    def __str__(self):
        return f"{self.full_name} ({self.email})"


class DashboardSavedFilter(models.Model):
    ROLE_CHOICES = [
        ("all", "All Views"),
        ("sales", "Sales"),
        ("ops", "Ops"),
    ]
    ACTIVITY_CHOICES = [
        ("all", "All"),
        ("contact", "Contacts"),
        ("quote", "Quotes"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard_saved_filters",
    )
    name = models.CharField(max_length=80)
    period_days = models.PositiveSmallIntegerField(default=7)
    activity_filter = models.CharField(max_length=16, choices=ACTIVITY_CHOICES, default="all")
    role_view = models.CharField(max_length=16, choices=ROLE_CHOICES, default="all")
    search_query = models.CharField(max_length=200, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = ("user", "name")
        verbose_name = "Dashboard Saved Filter"
        verbose_name_plural = "Dashboard Saved Filters"

    def __str__(self):
        return f"{self.user} · {self.name}"


class UpdatesSubscriber(models.Model):
    email = models.EmailField(unique=True)
    source = models.CharField(max_length=50, default="footer")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Updates Subscriber"
        verbose_name_plural = "Updates Subscribers"

    def __str__(self):
        return self.email
