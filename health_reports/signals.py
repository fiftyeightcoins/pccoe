from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import HealthReport, HealthAdvisory, Notification
from django.core.mail import send_mail
from django.conf import settings

@receiver(post_save, sender=HealthReport)
def notify_on_report_status_change(sender, instance, created, **kwargs):
    # Notify when admin updates report status
    if not created and instance.verified_by:
        Notification.objects.create(
            user=instance.reporter,
            notification_type='report_update',
            title=f'Report Status: {instance.get_status_display()}',
            message=f'Your report from {instance.location} has been updated.',
            related_report=instance
        )

@receiver(post_save, sender=HealthAdvisory)
def notify_on_new_advisory(sender, instance, created, **kwargs):
    # Notify users in affected region when new advisory is created
    if created and instance.is_active:
        from django.contrib.auth.models import User
        affected_users = User.objects.filter(
            reports__location__icontains=instance.region
        ).distinct()
        
        for user in affected_users:
            Notification.objects.create(
                user=user,
                notification_type='advisory',
                title=f'New Health Advisory: {instance.title}',
                message=instance.description[:200]
            )