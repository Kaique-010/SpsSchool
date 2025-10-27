from rest_framework import serializers
from .models import Module, Training, Video, UserProgress, UserCertificate
from users.serializers import UserProfileSerializer

class VideoSerializer(serializers.ModelSerializer):
    """
    Serializer para vídeos
    """
    youtube_id = serializers.ReadOnlyField()
    user_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'youtube_url', 'youtube_id', 'duration_seconds',
            'order_index', 'is_active', 'created_at', 'user_progress'
        ]
    
    def get_user_progress(self, obj):
        """Retorna o progresso do usuário para este vídeo"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            progress = obj.get_user_progress(request.user)
            if progress:
                return UserProgressSerializer(progress).data
        return None

class TrainingSerializer(serializers.ModelSerializer):
    """
    Serializer para treinamentos
    """
    videos = VideoSerializer(many=True, read_only=True)
    total_videos = serializers.ReadOnlyField()
    user_progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Training
        fields = [
            'id', 'title', 'description', 'duration_minutes', 'order_index',
            'is_active', 'created_at', 'videos', 'total_videos', 'user_progress_percentage'
        ]
    
    def get_user_progress_percentage(self, obj):
        """Retorna a porcentagem de progresso do usuário neste treinamento"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_user_progress(request.user)
        return 0

class TrainingListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para lista de treinamentos
    """
    total_videos = serializers.ReadOnlyField()
    user_progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Training
        fields = [
            'id', 'title', 'description', 'duration_minutes', 'order_index',
            'total_videos', 'user_progress_percentage'
        ]
    
    def get_user_progress_percentage(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_user_progress(request.user)
        return 0

class ModuleSerializer(serializers.ModelSerializer):
    """
    Serializer para módulos com treinamentos
    """
    trainings = TrainingListSerializer(many=True, read_only=True)
    total_trainings = serializers.ReadOnlyField()
    total_videos = serializers.ReadOnlyField()
    
    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'category', 'order_index',
            'is_active', 'created_at', 'trainings', 'total_trainings', 'total_videos'
        ]

class ModuleListSerializer(serializers.ModelSerializer):
    """
    Serializer simplificado para lista de módulos
    """
    total_trainings = serializers.ReadOnlyField()
    total_videos = serializers.ReadOnlyField()
    
    class Meta:
        model = Module
        fields = [
            'id', 'title', 'description', 'category', 'order_index',
            'total_trainings', 'total_videos'
        ]

class UserProgressSerializer(serializers.ModelSerializer):
    """
    Serializer para progresso do usuário
    """
    video_title = serializers.CharField(source='video.title', read_only=True)
    training_title = serializers.CharField(source='video.training.title', read_only=True)
    module_title = serializers.CharField(source='video.training.module.title', read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = UserProgress
        fields = [
            'id', 'progress_seconds', 'completed', 'last_watched', 'completed_at',
            'video_title', 'training_title', 'module_title', 'progress_percentage'
        ]
        read_only_fields = ['id', 'last_watched']

class UserProgressUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualizar progresso do usuário
    """
    class Meta:
        model = UserProgress
        fields = ['progress_seconds', 'completed']
    
    def update(self, instance, validated_data):
        """Atualiza o progresso e marca como concluído se necessário"""
        from django.utils import timezone
        
        instance.progress_seconds = validated_data.get('progress_seconds', instance.progress_seconds)
        
        # Se foi marcado como concluído e ainda não estava
        if validated_data.get('completed', False) and not instance.completed:
            instance.completed = True
            instance.completed_at = timezone.now()
        
        instance.save()
        return instance

class UserCertificateSerializer(serializers.ModelSerializer):
    """
    Serializer para certificados do usuário
    """
    user = UserProfileSerializer(read_only=True)
    training = TrainingListSerializer(read_only=True)
    
    class Meta:
        model = UserCertificate
        fields = [
            'id', 'certificate_code', 'issued_at', 'user', 'training'
        ]
        read_only_fields = ['id', 'certificate_code', 'issued_at']

class DashboardStatsSerializer(serializers.Serializer):
    """
    Serializer para estatísticas do dashboard
    """
    total_modules = serializers.IntegerField()
    total_trainings = serializers.IntegerField()
    total_videos = serializers.IntegerField()
    completed_videos = serializers.IntegerField()
    in_progress_videos = serializers.IntegerField()
    certificates_earned = serializers.IntegerField()
    overall_progress = serializers.FloatField()
    recent_activity = serializers.ListField()