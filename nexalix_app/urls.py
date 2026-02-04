from django.urls import path
from . import views

urlpatterns = [ 
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('services/', views.services, name='services'),
     path("services/<slug:slug>/", views.service_detail, name="service_detail"),
    path('industries/', views.industries, name='industries'),
    path('how_we_work/', views.how_we_work, name='how_we_work'),
    path('why_choose_us/', views.why_choose_us, name='why_choose_us'),
    path('contact/', views.contact, name='contact'),
    path('web_dev/', views.web_dev, name='web_dev'),
    path('mobile_app/', views.mobile_app, name='mobile_app'),
    path('digital_marketing/', views.digital_marketing, name='digital_marketing'),
    path('seo/', views.seo, name='seo'),
    path('it_consult/', views.it_consult, name='it_consult'),
    path('cloud/', views.cloud, name='cloud'),
    path('syste_dev/', views.syste_dev, name='syste_dev'),  
    path('ai_training/', views.ai_training, name='ai_training'),
]