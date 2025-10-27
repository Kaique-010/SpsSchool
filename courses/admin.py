from django.contrib import admin
from .models import Module, Training, Video, UserProgress, UserCertificate

class VideoInline(admin.TabularInline):
    """Inline para vídeos dentro do treinamento"""
    model = Video
    extra = 1
    fields = ['title', 'youtube_url', 'duration_seconds', 'order_index', 'is_active']
    ordering = ['order_index']

class TrainingInline(admin.TabularInline):
    """Inline para treinamentos dentro do módulo"""
    model = Training
    extra = 1
    fields = ['title', 'description', 'duration_minutes', 'order_index', 'is_active']
    ordering = ['order_index']

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    """Admin para módulos"""
    list_display = ['title', 'category', 'order_index', 'total_trainings', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'category']
    ordering = ['order_index', 'title']
    inlines = [TrainingInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('title', 'description', 'category')
        }),
        ('Configurações', {
            'fields': ('order_index', 'is_active')
        }),
    )

@admin.register(Training)
class TrainingAdmin(admin.ModelAdmin):
    """Admin para treinamentos"""
    list_display = ['title', 'module', 'duration_minutes', 'order_index', 'total_videos', 'is_active', 'created_at']
    list_filter = ['module', 'is_active', 'created_at']
    search_fields = ['title', 'description', 'module__title']
    ordering = ['module', 'order_index', 'title']
    inlines = [VideoInline]
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('module', 'title', 'description')
        }),
        ('Configurações', {
            'fields': ('duration_minutes', 'order_index', 'is_active')
        }),
    )

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    """Admin para vídeos"""
    list_display = ['title', 'training', 'youtube_id', 'duration_seconds', 'order_index', 'is_active', 'created_at']
    list_filter = ['training__module', 'training', 'is_active', 'created_at']
    search_fields = ['title', 'training__title', 'training__module__title']
    ordering = ['training', 'order_index', 'title']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('training', 'title', 'youtube_url')
        }),
        ('Configurações', {
            'fields': ('duration_seconds', 'order_index', 'is_active')
        }),
    )
    
    readonly_fields = ['youtube_id']

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    """Admin para progresso dos usuários"""
    list_display = ['user', 'video', 'progress_percentage', 'completed', 'last_watched']
    list_filter = ['completed', 'video__training__module', 'video__training', 'last_watched']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'video__title']
    ordering = ['-last_watched']
    
    readonly_fields = ['progress_percentage']

@admin.register(UserCertificate)
class UserCertificateAdmin(admin.ModelAdmin):
    """Admin para certificados dos usuários"""
    list_display = ['user', 'training', 'certificate_code', 'issued_at']
    list_filter = ['training__module', 'training', 'issued_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'training__title', 'certificate_code']
    ordering = ['-issued_at']
    
    readonly_fields = ['certificate_code', 'issued_at']
