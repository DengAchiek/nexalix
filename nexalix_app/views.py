from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    HeroSection, Service, Testimonial, AboutSection, ProcessStep,
    Industry, TechnologyCategory, CaseStudy, NewsletterSignup,
    Statistic, BlogPost, Partner, Award, ContactCTA,
    ServiceFeature, ServiceTechnology, PricingPlan
)
# If you have these models, import them:
# from .models import AboutPage, CompanyValue, ContactInfo, ContactMessage

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
    
    # Get case studies
    case_studies = CaseStudy.objects.filter(is_active=True).order_by('order')[:2]
    
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
    # If you have AboutPage model, use it:
    # about_page = AboutPage.objects.first()
    # values = CompanyValue.objects.all()
    # return render(request, "about.html", {"about": about_page, "values": values})
    
    # Otherwise, just render the template:
    return render(request, "about.html")

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
    return render(request, 'industries.html')

def how_we_work(request):
    """How We Work page view"""
    return render(request, 'how_we_work.html')

def why_choose_us(request):
    """Why Choose Us page view"""
    return render(request, 'why_choose_us.html')

def contact(request):
    """Contact page view"""
   
    
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        service = request.POST.get("service")
        message = request.POST.get("message")

       
        try:
            send_mail(
                subject=f"New Contact Message – {service}",
                message=f"""
Name: {full_name}
Email: {email}
Service: {service}

Message:
{message}
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL] if hasattr(settings, 'CONTACT_EMAIL') else [settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
        except Exception as e:
            print(f"Email error: {e}")
        
        return redirect("contact")
    
    # If you have contact_info, pass it:
    # return render(request, "contact.html", {"contact_info": contact_info})
    return render(request, "contact.html")



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