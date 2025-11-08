from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    """Extended user profile with role information"""
    ROLE_CHOICES = [
        ('user', 'Public User'),
        ('admin', 'Health Official/Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(max_length=15, blank=True)
    organization = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_admin(self):
        return self.role == 'admin'


class HealthReport(models.Model):
    """Health report submitted by users"""
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('verified', 'Verified'),
        ('investigating', 'Under Investigation'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]
    
    DISEASE_CHOICES = [
        ('respiratory', 'Respiratory Issues'),
        ('waterborne', 'Waterborne Diseases'),
        ('vector', 'Vector-borne Diseases'),
        ('heat_related', 'Heat-related Illness'),
        ('skin', 'Skin Conditions'),
        ('cardiovascular', 'Cardiovascular Issues'),
        ('mental_health', 'Mental Health Issues'),
        ('other', 'Other'),
    ]
    
    ENVIRONMENTAL_CAUSE_CHOICES = [
        ('air_pollution', 'Air Pollution'),
        ('water_contamination', 'Contaminated Water'),
        ('heatwave', 'Extreme Heat/Heatwave'),
        ('flooding', 'Flooding'),
        ('drought', 'Drought'),
        ('poor_sanitation', 'Poor Sanitation'),
        ('waste_pollution', 'Waste Pollution'),
        ('climate_stress', 'General Climate Stress'),
        ('unknown', 'Unknown'),
    ]
    
    # Reporter Information
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    
    # Report Details
    disease_type = models.CharField(max_length=50, choices=DISEASE_CHOICES)
    symptoms = models.TextField(help_text="Describe the symptoms experienced")
    environmental_cause = models.CharField(max_length=50, choices=ENVIRONMENTAL_CAUSE_CHOICES)
    
    # Location Information
    location = models.CharField(max_length=200, help_text="City, District, or specific area")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Additional Information
    affected_count = models.IntegerField(default=1, help_text="Number of people affected")
    additional_notes = models.TextField(blank=True)
    
    # Status and Management
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, help_text="Notes from health officials")
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='verified_reports')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['disease_type']),
            models.Index(fields=['environmental_cause']),
        ]
    
    def __str__(self):
        return f"{self.get_disease_type_display()} - {self.location} ({self.created_at.date()})"
    
    def mark_as_resolved(self, admin_user):
        """Mark report as resolved"""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.verified_by = admin_user
        self.save()


class HealthAdvisory(models.Model):
    """Public health advisories issued by admins"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    region = models.CharField(max_length=200, help_text="Affected region")
    related_cause = models.CharField(max_length=50, choices=HealthReport.ENVIRONMENTAL_CAUSE_CHOICES)
    preventive_measures = models.TextField()
    
    issued_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Health Advisories'
    
    def __str__(self):
        return f"{self.title} - {self.region}"


class Notification(models.Model):
    """User notifications"""
    NOTIFICATION_TYPES = [
        ('report_update', 'Report Status Update'),
        ('advisory', 'Health Advisory'),
        ('response', 'Admin Response'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_report = models.ForeignKey(HealthReport, on_delete=models.CASCADE, null=True, blank=True)
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
