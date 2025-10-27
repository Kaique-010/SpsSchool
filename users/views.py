from django.shortcuts import render
from django.contrib.auth import login, logout
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.openapi import OpenApiTypes
from .models import User
from .serializers import (
    UserSerializer, UserProfileSerializer, LoginSerializer, 
    ChangePasswordSerializer, CustomTokenObtainPairSerializer
)
from core.models import AuditLog

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    View customizada para login JWT que inclui dados do usuário na resposta
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    @extend_schema(
        summary="Login JWT",
        description="Autentica o usuário e retorna tokens JWT (access e refresh) para uso nas APIs.",
        tags=['Autenticação'],
        examples=[
            OpenApiExample(
                'Exemplo de requisição',
                value={
                    "username": "usuario@exemplo.com",
                    "password": "minhasenha123"
                }
            ),
            OpenApiExample(
                'Exemplo de resposta',
                value={
                    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
                }
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Log de auditoria para login
            email = request.data.get('email') or request.data.get('username')
            user = User.objects.get(email=email)
            AuditLog.objects.create(
                user=user,
                action='LOGIN',
                model_name='User',
                object_id=str(user.id),
                description=f'Login realizado via API',
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class UserListCreateView(generics.ListCreateAPIView):
    """
    Lista usuários ou cria novos usuários (apenas administradores).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Listar usuários",
        description="Retorna uma lista de todos os usuários do sistema (requer autenticação).",
        tags=['Usuários'],
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Criar usuário",
        description="Cria um novo usuário no sistema (apenas administradores podem criar usuários).",
        tags=['Usuários'],
        request=UserSerializer,
        responses={
            201: UserSerializer,
            400: "Dados inválidos",
            403: "Permissão negada"
        },
        examples=[
            OpenApiExample(
                'Exemplo de requisição',
                value={
                    "username": "novousuario@exemplo.com",
                    "email": "novousuario@exemplo.com",
                    "first_name": "João",
                    "last_name": "Silva",
                    "password": "senhasegura123",
                    "department": "TI",
                    "position": "Desenvolvedor"
                }
            )
        ]
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def get_permissions(self):
        if self.request.method == 'POST':
            # Apenas admins podem criar usuários
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        user = serializer.save()
        # Log de auditoria
        AuditLog.objects.create(
            user=self.request.user,
            action='CREATE',
            model_name='User',
            object_id=str(user.id),
            description=f'Usuário {user.username} criado',
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Visualiza, atualiza ou remove um usuário específico.
    
    Usuários podem editar apenas seu próprio perfil, exceto administradores.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Detalhar usuário",
        description="Retorna os detalhes de um usuário específico.",
        tags=['Usuários'],
        responses={200: UserSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Atualizar usuário",
        description="Atualiza os dados de um usuário específico. Usuários podem editar apenas seu próprio perfil.",
        tags=['Usuários'],
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: "Dados inválidos",
            403: "Permissão negada"
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        summary="Atualizar parcialmente usuário",
        description="Atualiza parcialmente os dados de um usuário específico.",
        tags=['Usuários'],
        request=UserSerializer,
        responses={200: UserSerializer}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @extend_schema(
        summary="Deletar usuário",
        description="Remove um usuário do sistema (apenas administradores ou o próprio usuário).",
        tags=['Usuários'],
        responses={
            204: "Usuário removido com sucesso",
            403: "Permissão negada"
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
    
    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            # Apenas admins ou o próprio usuário podem editar/deletar
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated()]
    
    def get_object(self):
        obj = super().get_object()
        # Usuários só podem editar seu próprio perfil, exceto admins
        if not self.request.user.is_admin and obj != self.request.user:
            self.permission_denied(self.request)
        return obj
    
    def perform_update(self, serializer):
        user = serializer.save()
        # Log de auditoria
        AuditLog.objects.create(
            user=self.request.user,
            action='UPDATE',
            model_name='User',
            object_id=str(user.id),
            description=f'Usuário {user.username} atualizado',
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Visualiza e atualiza o perfil do usuário autenticado.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Visualizar perfil",
        description="Retorna os dados do perfil do usuário autenticado.",
        tags=['Perfil'],
        responses={200: UserProfileSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @extend_schema(
        summary="Atualizar perfil",
        description="Atualiza os dados do perfil do usuário autenticado.",
        tags=['Perfil'],
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer},
        examples=[
            OpenApiExample(
                'Exemplo de requisição',
                value={
                    "first_name": "João",
                    "last_name": "Silva",
                    "email": "joao.silva@exemplo.com",
                    "department": "TI",
                    "position": "Desenvolvedor Senior"
                }
            )
        ]
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @extend_schema(
        summary="Atualizar parcialmente perfil",
        description="Atualiza parcialmente os dados do perfil do usuário autenticado.",
        tags=['Perfil'],
        request=UserProfileSerializer,
        responses={200: UserProfileSerializer}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    def get_object(self):
        return self.request.user

@extend_schema(
    summary="Alterar senha",
    description="Permite que o usuário autenticado altere sua senha fornecendo a senha atual e a nova senha.",
    tags=['Perfil'],
    request=ChangePasswordSerializer,
    responses={
        200: {"description": "Senha alterada com sucesso"},
        400: "Dados inválidos"
    },
    examples=[
        OpenApiExample(
            'Exemplo de requisição',
            value={
                "old_password": "senhaatual123",
                "new_password": "novasenha456",
                "confirm_password": "novasenha456"
            }
        ),
        OpenApiExample(
            'Exemplo de resposta',
            value={
                "message": "Senha alterada com sucesso."
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """
    Endpoint para mudança de senha
    """
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        # Log de auditoria
        AuditLog.objects.create(
            user=user,
            action='UPDATE',
            model_name='User',
            object_id=str(user.id),
            description='Senha alterada',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return Response({'message': 'Senha alterada com sucesso.'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="Logout",
    description="Realiza o logout do usuário autenticado e registra a ação no log de auditoria.",
    tags=['Autenticação'],
    responses={
        200: {"description": "Logout realizado com sucesso"}
    },
    examples=[
        OpenApiExample(
            'Exemplo de resposta',
            value={
                "message": "Logout realizado com sucesso."
            }
        )
    ]
)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    Endpoint para logout
    """
    # Log de auditoria
    AuditLog.objects.create(
        user=request.user,
        action='LOGOUT',
        model_name='User',
        object_id=str(request.user.id),
        description='Logout realizado via API',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    return Response({'message': 'Logout realizado com sucesso.'}, status=status.HTTP_200_OK)

def get_client_ip(request):
    """Função auxiliar para obter IP do cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
