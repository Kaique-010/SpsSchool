from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Módulos
    path('modules/', views.ModuleListView.as_view(), name='module_list'),
    path('modules/<int:pk>/', views.ModuleDetailView.as_view(), name='module_detail'),
    
    # Treinamentos
    path('trainings/<int:pk>/', views.TrainingDetailView.as_view(), name='training_detail'),
    
    # Vídeos
    path('videos/<int:pk>/', views.VideoDetailView.as_view(), name='video_detail'),
    path('videos/<int:video_id>/progress/', views.update_video_progress, name='update_video_progress'),
    
    # Progresso do usuário
    path('progress/', views.user_progress_list, name='user_progress_list'),
    
    # Certificados
    path('certificates/', views.user_certificates, name='user_certificates'),
    
    # Dashboard
    path('dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
]