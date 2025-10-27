from rest_framework import serializers
from .models import SystemSettings, AuditLog, Notification, FAQ
from users.serializers import UserProfileSerializer

class SystemSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer para configurações do sistema
    """
    class Meta:
        model = SystemSettings
        fields = ['id', 'key', 'value', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer para logs de auditoria
    """
    user = UserProfileSerializer(read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'action', 'action_display', 'model_name', 'object_id',
            'description', 'ip_address', 'user_agent', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer para notificações
    """
    type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'type_display',
            'is_read', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']

class FAQSerializer(serializers.ModelSerializer):
    """
    Serializer para FAQs
    """
    class Meta:
        model = FAQ
        fields = [
            'id', 'question', 'answer', 'category', 'order_index',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']