from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Modelo customizado de usuário para o sistema de treinamento
    """
    ROLE_CHOICES = [
        ('employee', 'Funcionário'),
        ('instructor', 'Instrutor'),
        ('admin', 'Administrador'),
    ]
    
    email = models.EmailField(unique=True, verbose_name='Email')
    first_name = models.CharField(max_length=100, verbose_name='Nome')
    last_name = models.CharField(max_length=100, verbose_name='Sobrenome')
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='employee',
        verbose_name='Papel'
    )
    is_active = models.BooleanField(default=True, verbose_name='Ativo')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_instructor(self):
        return self.role == 'instructor'
    
    def is_employee(self):
        return self.role == 'employee'


class UserProfile(models.Model):
    """
    Perfil estendido do usuário
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    bio = models.TextField(max_length=500, blank=True, verbose_name='Biografia')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Avatar')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Telefone')
    department = models.CharField(max_length=100, blank=True, verbose_name='Departamento')
    position = models.CharField(max_length=100, blank=True, verbose_name='Cargo')
    hire_date = models.DateField(blank=True, null=True, verbose_name='Data de contratação')
    birth_date = models.DateField(blank=True, null=True, verbose_name='Data de nascimento')
    
    # Preferências
    theme_preference = models.CharField(
        max_length=10,
        choices=[('light', 'Claro'), ('dark', 'Escuro'), ('auto', 'Automático')],
        default='auto',
        verbose_name='Tema preferido'
    )
    language_preference = models.CharField(
        max_length=10,
        choices=[('pt-br', 'Português'), ('en', 'English')],
        default='pt-br',
        verbose_name='Idioma preferido'
    )
    email_notifications = models.BooleanField(default=True, verbose_name='Notificações por email')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atualizado em')
    
    class Meta:
        verbose_name = 'Perfil do Usuário'
        verbose_name_plural = 'Perfis dos Usuários'
        db_table = 'user_profiles'
    
    def __str__(self):
        return f"Perfil de {self.user.full_name}"
