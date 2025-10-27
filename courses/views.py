from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Count, Avg
from django.utils import timezone
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.openapi import OpenApiTypes
from .models import Module, Training, Video, UserProgress, UserCertificate
from .serializers import (
    ModuleSerializer, ModuleListSerializer, TrainingSerializer, 
    TrainingListSerializer, VideoSerializer, UserProgressSerializer,
    UserProgressUpdateSerializer, UserCertificateSerializer,
    DashboardStatsSerializer
)
from core.models import AuditLog

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class ModuleListView(generics.ListAPIView):
    """
    Lista todos os módulos ativos disponíveis no sistema.
    
    Permite filtrar por categoria e buscar por título ou descrição.
    """
    serializer_class = ModuleListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    @extend_schema(
        summary="Listar módulos",
        description="Retorna uma lista paginada de todos os módulos ativos disponíveis no sistema.",
        parameters=[
            OpenApiParameter(
                name='category',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filtrar por categoria do módulo'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Buscar por título ou descrição do módulo'
            ),
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Número da página'
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Quantidade de itens por página (máximo 100)'
            ),
        ],
        tags=['Módulos'],
        examples=[
            OpenApiExample(
                'Exemplo de resposta',
                value={
                    "count": 10,
                    "next": "http://localhost:8000/api/courses/modules/?page=2",
                    "previous": None,
                    "results": [
                        {
                            "id": 1,
                            "title": "Segurança no Trabalho",
                            "description": "Módulo sobre normas de segurança",
                            "category": "Segurança",
                            "thumbnail": "/media/thumbnails/modulo1.jpg",
                            "duration_minutes": 120,
                            "trainings_count": 5,
                            "videos_count": 15
                        }
                    ]
                }
            )
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Module.objects.filter(is_active=True)
        
        # Filtros
        category = self.request.query_params.get('category')
        search = self.request.query_params.get('search')
        
        if category:
            queryset = queryset.filter(category__icontains=category)
        
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset.order_by('order_index', 'title')

class ModuleDetailView(generics.RetrieveAPIView):
    """
    Retorna os detalhes completos de um módulo específico, incluindo seus treinamentos.
    """
    queryset = Module.objects.filter(is_active=True)
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Detalhar módulo",
        description="Retorna os detalhes completos de um módulo específico, incluindo todos os treinamentos associados.",
        tags=['Módulos'],
        examples=[
            OpenApiExample(
                'Exemplo de resposta',
                value={
                    "id": 1,
                    "title": "Segurança no Trabalho",
                    "description": "Módulo completo sobre normas de segurança",
                    "category": "Segurança",
                    "thumbnail": "/media/thumbnails/modulo1.jpg",
                    "duration_minutes": 120,
                    "trainings": [
                        {
                            "id": 1,
                            "title": "Equipamentos de Proteção Individual",
                            "description": "Como usar EPIs corretamente",
                            "duration_minutes": 30,
                            "videos_count": 3
                        }
                    ]
                }
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        
        # Log de auditoria
        module = self.get_object()
        AuditLog.objects.create(
            user=request.user,
            action='VIEW',
            model_name='Module',
            object_id=str(module.id),
            description=f'Módulo {module.title} visualizado',
            ip_address=self.get_client_ip(),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return response
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

class TrainingDetailView(generics.RetrieveAPIView):
    """
    Retorna os detalhes completos de um treinamento específico, incluindo seus vídeos.
    """
    queryset = Training.objects.filter(is_active=True)
    serializer_class = TrainingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Detalhar treinamento",
        description="Retorna os detalhes completos de um treinamento específico, incluindo todos os vídeos associados.",
        tags=['Treinamentos'],
        examples=[
            OpenApiExample(
                'Exemplo de resposta',
                value={
                    "id": 1,
                    "title": "Equipamentos de Proteção Individual",
                    "description": "Como usar EPIs corretamente",
                    "duration_minutes": 30,
                    "module": {
                        "id": 1,
                        "title": "Segurança no Trabalho"
                    },
                    "videos": [
                        {
                            "id": 1,
                            "title": "Introdução aos EPIs",
                            "description": "Conceitos básicos",
                            "duration_seconds": 300,
                            "video_url": "/media/videos/video1.mp4"
                        }
                    ]
                }
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        
        # Log de auditoria
        training = self.get_object()
        AuditLog.objects.create(
            user=request.user,
            action='VIEW',
            model_name='Training',
            object_id=str(training.id),
            description=f'Treinamento {training.title} visualizado',
            ip_address=self.get_client_ip(),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return response
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

class VideoDetailView(generics.RetrieveAPIView):
    """
    Retorna os detalhes completos de um vídeo específico.
    """
    queryset = Video.objects.filter(is_active=True)
    serializer_class = VideoSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @extend_schema(
        summary="Detalhar vídeo",
        description="Retorna os detalhes completos de um vídeo específico, incluindo informações do treinamento e módulo.",
        tags=['Vídeos'],
        examples=[
            OpenApiExample(
                'Exemplo de resposta',
                value={
                    "id": 1,
                    "title": "Introdução aos EPIs",
                    "description": "Conceitos básicos sobre equipamentos de proteção",
                    "duration_seconds": 300,
                    "video_url": "/media/videos/video1.mp4",
                    "thumbnail": "/media/thumbnails/video1.jpg",
                    "training": {
                        "id": 1,
                        "title": "Equipamentos de Proteção Individual",
                        "module": {
                            "id": 1,
                            "title": "Segurança no Trabalho"
                        }
                    }
                }
            )
        ]
    )
    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        
        # Log de auditoria
        video = self.get_object()
        AuditLog.objects.create(
            user=request.user,
            action='VIEW',
            model_name='Video',
            object_id=str(video.id),
            description=f'Vídeo {video.title} visualizado',
            ip_address=self.get_client_ip(),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        return response
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

@extend_schema(
    methods=['POST', 'PUT'],
    summary="Atualizar progresso do vídeo",
    description="Atualiza o progresso de visualização de um vídeo específico pelo usuário autenticado.",
    tags=['Progresso'],
    request=UserProgressUpdateSerializer,
    responses={
        200: UserProgressSerializer,
        400: "Dados inválidos",
        404: "Vídeo não encontrado"
    },
    examples=[
        OpenApiExample(
            'Exemplo de requisição',
            value={
                "progress_seconds": 150,
                "completed": False
            }
        ),
        OpenApiExample(
            'Exemplo de resposta',
            value={
                "id": 1,
                "user": 1,
                "video": 1,
                "progress_seconds": 150,
                "progress_percentage": 50.0,
                "completed": False,
                "last_watched": "2023-10-27T10:30:00Z"
            }
        )
    ]
)
@api_view(['POST', 'PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_video_progress(request, video_id):
    """
    Endpoint para atualizar progresso do vídeo
    """
    video = get_object_or_404(Video, id=video_id, is_active=True)
    
    # Busca ou cria o progresso do usuário
    progress, created = UserProgress.objects.get_or_create(
        user=request.user,
        video=video,
        defaults={'progress_seconds': 0}
    )
    
    serializer = UserProgressUpdateSerializer(progress, data=request.data, partial=True)
    if serializer.is_valid():
        progress = serializer.save()
        
        # Log de auditoria
        action = 'COMPLETE' if progress.completed else 'UPDATE'
        AuditLog.objects.create(
            user=request.user,
            action=action,
            model_name='UserProgress',
            object_id=str(progress.id),
            description=f'Progresso do vídeo {video.title} atualizado',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Verifica se o treinamento foi completado para gerar certificado
        if progress.completed:
            check_training_completion(request.user, video.training)
        
        return Response(UserProgressSerializer(progress).data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(
    summary="Listar progresso do usuário",
    description="Retorna uma lista paginada do progresso de visualização de vídeos do usuário autenticado.",
    parameters=[
        OpenApiParameter(
            name='completed',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description='Filtrar por vídeos completados (true) ou não completados (false)'
        ),
        OpenApiParameter(
            name='module_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Filtrar por ID do módulo'
        ),
        OpenApiParameter(
            name='training_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Filtrar por ID do treinamento'
        ),
    ],
    tags=['Progresso'],
    responses={200: UserProgressSerializer(many=True)},
    examples=[
        OpenApiExample(
            'Exemplo de resposta',
            value={
                "count": 25,
                "next": "http://localhost:8000/api/courses/progress/?page=2",
                "previous": None,
                "results": [
                    {
                        "id": 1,
                        "user": 1,
                        "video": {
                            "id": 1,
                            "title": "Introdução aos EPIs",
                            "training": {
                                "title": "Equipamentos de Proteção Individual",
                                "module": {
                                    "title": "Segurança no Trabalho"
                                }
                            }
                        },
                        "progress_seconds": 300,
                        "progress_percentage": 100.0,
                        "completed": True,
                        "last_watched": "2023-10-27T10:30:00Z"
                    }
                ]
            }
        )
    ]
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_progress_list(request):
    """
    Endpoint para listar progresso do usuário
    """
    progress_list = UserProgress.objects.filter(user=request.user).select_related(
        'video', 'video__training', 'video__training__module'
    ).order_by('-last_watched')
    
    # Filtros
    completed = request.query_params.get('completed')
    module_id = request.query_params.get('module_id')
    training_id = request.query_params.get('training_id')
    
    if completed is not None:
        progress_list = progress_list.filter(completed=completed.lower() == 'true')
    
    if module_id:
        progress_list = progress_list.filter(video__training__module_id=module_id)
    
    if training_id:
        progress_list = progress_list.filter(video__training_id=training_id)
    
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(progress_list, request)
    
    if page is not None:
        serializer = UserProgressSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    serializer = UserProgressSerializer(progress_list, many=True)
    return Response(serializer.data)

@extend_schema(
    summary="Listar certificados do usuário",
    description="Retorna uma lista de todos os certificados emitidos para o usuário autenticado.",
    tags=['Certificados'],
    responses={200: UserCertificateSerializer(many=True)},
    examples=[
        OpenApiExample(
            'Exemplo de resposta',
            value=[
                {
                    "id": 1,
                    "user": 1,
                    "training": {
                        "id": 1,
                        "title": "Equipamentos de Proteção Individual",
                        "module": {
                            "title": "Segurança no Trabalho"
                        }
                    },
                    "certificate_code": "CERT-2023-001",
                    "issued_at": "2023-10-27T15:30:00Z"
                }
            ]
        )
    ]
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_certificates(request):
    """
    Endpoint para listar certificados do usuário
    """
    certificates = UserCertificate.objects.filter(user=request.user).select_related(
        'training', 'training__module'
    ).order_by('-issued_at')
    
    serializer = UserCertificateSerializer(certificates, many=True)
    return Response(serializer.data)

@extend_schema(
    summary="Estatísticas do dashboard",
    description="Retorna estatísticas gerais e do progresso do usuário para exibição no dashboard.",
    tags=['Dashboard'],
    responses={200: DashboardStatsSerializer},
    examples=[
        OpenApiExample(
            'Exemplo de resposta',
            value={
                "total_modules": 5,
                "total_trainings": 15,
                "total_videos": 45,
                "completed_videos": 20,
                "in_progress_videos": 8,
                "certificates_earned": 3,
                "overall_progress": 44.44,
                "recent_activity": [
                    {
                        "video_title": "Introdução aos EPIs",
                        "training_title": "Equipamentos de Proteção Individual",
                        "module_title": "Segurança no Trabalho",
                        "progress_percentage": 100.0,
                        "completed": True,
                        "last_watched": "2023-10-27T10:30:00Z"
                    }
                ]
            }
        )
    ]
)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """
    Endpoint para estatísticas do dashboard
    """
    user = request.user
    
    # Estatísticas gerais
    total_modules = Module.objects.filter(is_active=True).count()
    print(f"Total módulos ativos: {total_modules}")
    total_trainings = Training.objects.filter(is_active=True, module__is_active=True).count()
    total_videos = Video.objects.filter(is_active=True, training__is_active=True, training__module__is_active=True).count()
    
    # Progresso do usuário
    user_progress = UserProgress.objects.filter(user=user)
    completed_videos = user_progress.filter(completed=True).count()
    in_progress_videos = user_progress.filter(completed=False, progress_seconds__gt=0).count()
    
    # Certificados
    certificates_earned = UserCertificate.objects.filter(user=user).count()
    
    # Progresso geral
    overall_progress = (completed_videos / total_videos * 100) if total_videos > 0 else 0
    
    # Atividade recente
    recent_activity = user_progress.order_by('-last_watched')[:5]
    recent_activity_data = []
    for progress in recent_activity:
        recent_activity_data.append({
            'video_title': progress.video.title,
            'training_title': progress.video.training.title,
            'module_title': progress.video.training.module.title,
            'progress_percentage': progress.progress_percentage,
            'completed': progress.completed,
            'last_watched': progress.last_watched
        })
    
    stats = {
        'total_modules': total_modules,
        'total_trainings': total_trainings,
        'total_videos': total_videos,
        'completed_videos': completed_videos,
        'in_progress_videos': in_progress_videos,
        'certificates_earned': certificates_earned,
        'overall_progress': round(overall_progress, 2),
        'recent_activity': recent_activity_data
    }
    
    serializer = DashboardStatsSerializer(stats)
    return Response(serializer.data)

def check_training_completion(user, training):
    """
    Verifica se o treinamento foi completado e gera certificado
    """
    total_videos = training.videos.filter(is_active=True).count()
    completed_videos = UserProgress.objects.filter(
        user=user,
        video__training=training,
        completed=True
    ).count()
    
    # Se completou todos os vídeos e ainda não tem certificado
    if total_videos > 0 and completed_videos == total_videos:
        certificate, created = UserCertificate.objects.get_or_create(
            user=user,
            training=training
        )
        
        if created:
            # Log de auditoria para certificado
            AuditLog.objects.create(
                user=user,
                action='CREATE',
                model_name='UserCertificate',
                object_id=str(certificate.id),
                description=f'Certificado emitido para o treinamento {training.title}',
                ip_address='127.0.0.1',  # Sistema interno
                user_agent='Sistema'
            )

def get_client_ip(request):
    """Função auxiliar para obter IP do cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
