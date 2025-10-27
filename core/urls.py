from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Página inicial
    path('', views.home, name='home'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Módulos e treinamentos (web)
    path('modules/', views.modules_list, name='modules_list'),
    path('modules/<int:module_id>/', views.module_detail, name='module_detail'),
    path('videos/<int:video_id>/', views.video_detail, name='video_detail'),
    
    # Perfil do usuário
    path('profile/', views.profile, name='profile'),
    
    # Autenticação (web)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Certificados
    path('certificates/', views.certificates, name='certificates'),

    
    # FAQ
    path('faq/', views.faq, name='faq'),
]