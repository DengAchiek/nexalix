from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.utils.text import slugify
from .models import (
    HeroSection, Service, Testimonial, AboutSection, ProcessStep,
    Industry, TechnologyCategory, CaseStudy, NewsletterSignup,
    Statistic, BlogPost, Partner, Award, ContactCTA,
    ServiceFeature, ServiceTechnology, PricingPlan, ContactMessage
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
    
    # Get case studies for home page
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
        # Get admin email(s)
        admin_emails = [settings.DEFAULT_FROM_EMAIL]
        
        # You can add specific admin emails in settings
        if hasattr(settings, 'ADMIN_EMAILS'):
            admin_emails = settings.ADMIN_EMAILS
        
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
