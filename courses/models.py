from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

class Module(models.Model):
    """
    Modelo para módulos de treinamento
    """
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(blank=True, verbose_name='Descrição')
    category = models.CharField(max_length=100, verbose_name='Categoria')
    order_index = models.IntegerField(default=0, verbose_name='Ordem')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Módulo'
        verbose_name_plural = 'Módulos'
        db_table = 'modules'
        ordering = ['order_index', 'title']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['order_index']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def total_trainings(self):
        return self.trainings.filter(is_active=True).count()
    
    @property
    def total_videos(self):
        return sum(training.total_videos for training in self.trainings.filter(is_active=True))

class Training(models.Model):
    """
    Modelo para treinamentos dentro de um módulo
    """
    module = models.ForeignKey(
        Module, 
        on_delete=models.CASCADE, 
        related_name='trainings',
        verbose_name='Módulo'
    )
    title = models.CharField(max_length=200, verbose_name='Título')
    description = models.TextField(blank=True, verbose_name='Descrição')
    duration_minutes = models.IntegerField(default=0, verbose_name='Duração (minutos)')
    order_index = models.IntegerField(default=0, verbose_name='Ordem')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Treinamento'
        verbose_name_plural = 'Treinamentos'
        db_table = 'trainings'
        ordering = ['order_index', 'title']
        indexes = [
            models.Index(fields=['module_id']),
            models.Index(fields=['order_index']),
        ]
    
    def __str__(self):
        return f"{self.module.title} - {self.title}"
    
    @property
    def total_videos(self):
        return self.videos.filter(is_active=True).count()
    
    def get_user_progress(self, user):
        """Calcula o progresso do usuário neste treinamento"""
        total_videos = self.total_videos
        if total_videos == 0:
            return 0
        
        completed_videos = UserProgress.objects.filter(
            user=user,
            video__training=self,
            completed=True
        ).count()
        
        return (completed_videos / total_videos) * 100

class Video(models.Model):
    """
    Modelo para vídeos de um treinamento
    """
    training = models.ForeignKey(
        Training, 
        on_delete=models.CASCADE, 
        related_name='videos',
        verbose_name='Treinamento'
    )
    title = models.CharField(max_length=200, verbose_name='Título')
    youtube_url = models.URLField(max_length=500, verbose_name='URL do YouTube')
    duration_seconds = models.IntegerField(default=0, verbose_name='Duração (segundos)')
    order_index = models.IntegerField(default=0, verbose_name='Ordem')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Vídeo'
        verbose_name_plural = 'Vídeos'
        db_table = 'videos'
        ordering = ['order_index', 'title']
        indexes = [
            models.Index(fields=['training_id']),
            models.Index(fields=['order_index']),
        ]
    
    def __str__(self):
        return f"{self.training.title} - {self.title}"
    
    @property
    def youtube_id(self):
        """Extrai o ID do vídeo do YouTube da URL"""
        if 'youtube.com/watch?v=' in self.youtube_url:
            return self.youtube_url.split('watch?v=')[1].split('&')[0]
        elif 'youtu.be/' in self.youtube_url:
            return self.youtube_url.split('youtu.be/')[1].split('?')[0]
        return None
    
    def get_user_progress(self, user):
        """Retorna o progresso do usuário neste vídeo"""
        try:
            progress = UserProgress.objects.get(user=user, video=self)
            return progress
        except UserProgress.DoesNotExist:
            return None

class UserProgress(models.Model):
    """
    Modelo para controlar o progresso do usuário nos vídeos
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='progress',
        verbose_name='Usuário'
    )
    video = models.ForeignKey(
        Video, 
        on_delete=models.CASCADE, 
        related_name='user_progress',
        verbose_name='Vídeo'
    )
    progress_seconds = models.IntegerField(default=0, verbose_name='Progresso (segundos)')
    completed = models.BooleanField(default=False, verbose_name='Concluído')
    last_watched = models.DateTimeField(auto_now=True, verbose_name='Última visualização')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Concluído em')
    
    class Meta:
        verbose_name = 'Progresso do Usuário'
        verbose_name_plural = 'Progressos dos Usuários'
        db_table = 'user_progress'
        unique_together = ['user', 'video']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['video_id']),
            models.Index(fields=['completed']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.video.title}"
    
    @property
    def progress_percentage(self):
        """Calcula a porcentagem de progresso"""
        if self.video.duration_seconds == 0:
            return 0
        return min((self.progress_seconds / self.video.duration_seconds) * 100, 100)

class UserCertificate(models.Model):
    """
    Modelo para certificados dos usuários
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='certificates',
        verbose_name='Usuário'
    )
    training = models.ForeignKey(
        Training, 
        on_delete=models.CASCADE, 
        related_name='certificates',
        verbose_name='Treinamento'
    )
    certificate_code = models.CharField(
        max_length=50, 
        unique=True, 
        default=uuid.uuid4,
        verbose_name='Código do Certificado'
    )
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name='Emitido em')
    
    class Meta:
        verbose_name = 'Certificado'
        verbose_name_plural = 'Certificados'
        db_table = 'user_certificates'
        unique_together = ['user', 'training']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['training_id']),
            models.Index(fields=['certificate_code']),
        ]
    
    def __str__(self):
        return f"Certificado: {self.user.full_name} - {self.training.title}"
