from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'users'

urlpatterns = [
    # Autenticação JWT
    path('auth/login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', views.logout_view, name='logout'),
    
    # Gerenciamento de usuários
    path('', views.UserListCreateView.as_view(), name='user_list_create'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    
    # Perfil do usuário
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('change-password/', views.change_password, name='change_password'),
]