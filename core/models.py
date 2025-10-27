from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SystemSettings(models.Model):
    """
    Modelo para configurações do sistema
    """
    key = models.CharField(max_length=100, unique=True, verbose_name='Chave')
    value = models.TextField(verbose_name='Valor')
    description = models.TextField(blank=True, verbose_name='Descrição')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Configuração do Sistema'
        verbose_name_plural = 'Configurações do Sistema'
        db_table = 'system_settings'
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"

class AuditLog(models.Model):
    """
    Modelo para logs de auditoria do sistema
    """
    ACTION_CHOICES = [
        ('CREATE', 'Criar'),
        ('UPDATE', 'Atualizar'),
        ('DELETE', 'Deletar'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('VIEW', 'Visualizar'),
        ('COMPLETE', 'Completar'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='audit_logs',
        verbose_name='Usuário'
    )
    action = models.CharField(
        max_length=20, 
        choices=ACTION_CHOICES,
        verbose_name='Ação'
    )
    model_name = models.CharField(max_length=100, verbose_name='Modelo')
    object_id = models.CharField(max_length=100, blank=True, verbose_name='ID do Objeto')
    description = models.TextField(blank=True, verbose_name='Descrição')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP')
    user_agent = models.TextField(blank=True, verbose_name='User Agent')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Data/Hora')
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        db_table = 'audit_logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['action']),
            models.Index(fields=['model_name']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        user_name = self.user.full_name if self.user else 'Sistema'
        return f"{user_name} - {self.get_action_display()} - {self.model_name}"

class Notification(models.Model):
    """
    Modelo para notificações do sistema
    """
    TYPE_CHOICES = [
        ('INFO', 'Informação'),
        ('SUCCESS', 'Sucesso'),
        ('WARNING', 'Aviso'),
        ('ERROR', 'Erro'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications',
        verbose_name='Usuário'
    )
    title = models.CharField(max_length=200, verbose_name='Título')
    message = models.TextField(verbose_name='Mensagem')
    notification_type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES, 
        default='INFO',
        verbose_name='Tipo'
    )
    is_read = models.BooleanField(default=False, verbose_name='Lida')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criada em')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='Lida em')
    
    class Meta:
        verbose_name = 'Notificação'
        verbose_name_plural = 'Notificações'
        db_table = 'notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['is_read']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} - {self.title}"
    
    def mark_as_read(self):
        """Marca a notificação como lida"""
        from django.utils import timezone
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

class FAQ(models.Model):
    """
    Modelo para perguntas frequentes
    """
    question = models.CharField(max_length=500, verbose_name='Pergunta')
    answer = models.TextField(verbose_name='Resposta')
    category = models.CharField(max_length=100, verbose_name='Categoria')
    order_index = models.IntegerField(default=0, verbose_name='Ordem')
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        db_table = 'faqs'
        ordering = ['category', 'order_index', 'question']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['order_index']),
        ]
    
    def __str__(self):
        return self.question[:100]
