from django.contrib import admin
from .models import UserProfile, HealthReport, HealthAdvisory, Notification

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'organization', 'created_at']
    list_filter = ['role']
    search_fields = ['user__username', 'organization']

@admin.register(HealthReport)
class HealthReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'disease_type', 'location', 'status', 'reporter', 'created_at']
    list_filter = ['status', 'disease_type', 'environmental_cause', 'created_at']
    search_fields = ['location', 'symptoms', 'reporter__username']
    date_hierarchy = 'created_at'

@admin.register(HealthAdvisory)
class HealthAdvisoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'region', 'priority', 'is_active', 'created_at']
    list_filter = ['priority', 'is_active', 'related_cause']
    search_fields = ['title', 'region']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'user__username']