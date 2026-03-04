# nexalix_app/models.py
from django.db import models
from django.utils import timezone
from django.utils.text import slugify



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
    
    # Additional features
    key_features = models.TextField(blank=True, help_text="One feature per line")
    technologies = models.TextField(blank=True, help_text="Technologies used (comma-separated)")
    pricing_info = models.TextField(blank=True, help_text="Pricing information")
    
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
    avatar = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

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
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='case_studies/')
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated tags, e.g. Fintech, AI, Automation"
    )
    results = models.TextField(blank=True)
    link = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = "Case Studies"

    def __str__(self):
        return self.title

    def get_tags_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
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


class Partner(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(
        blank=True,
        help_text="Brief description shown on the homepage partner card"
    )
    logo = models.ImageField(upload_to='partners/', blank=True, null=True)
    website = models.URLField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

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
    submitted_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
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
