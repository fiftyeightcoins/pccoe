from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile, HealthReport, HealthAdvisory, Notification


class UserRegistrationForm(UserCreationForm):
    """User registration form"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone = forms.CharField(max_length=15, required=False)
    
    ROLE_CHOICES = [
        ('user', 'Public User'),
        ('admin', 'Health Official (requires approval)'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial='user')
    organization = forms.CharField(max_length=200, required=False, 
                                   help_text='Required for Health Officials')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            UserProfile.objects.create(
                user=user,
                role=self.cleaned_data['role'],
                phone=self.cleaned_data.get('phone', ''),
                organization=self.cleaned_data.get('organization', '')
            )
        return user


class HealthReportForm(forms.ModelForm):
    """Health report submission form"""
    class Meta:
        model = HealthReport
        fields = ['disease_type', 'symptoms', 'environmental_cause', 'location', 
                  'latitude', 'longitude', 'affected_count', 'additional_notes']
        widgets = {
            'symptoms': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe symptoms in detail...'}),
            'additional_notes': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Any additional information...'}),
            'location': forms.TextInput(attrs={'placeholder': 'City, District, or specific area'}),
            'latitude': forms.NumberInput(attrs={'step': '0.000001', 'placeholder': 'Optional'}),
            'longitude': forms.NumberInput(attrs={'step': '0.000001', 'placeholder': 'Optional'}),
        }


class AdminReportReviewForm(forms.ModelForm):
    """Form for admins to review and update reports"""
    class Meta:
        model = HealthReport
        fields = ['status', 'admin_notes']
        widgets = {
            'admin_notes': forms.Textarea(attrs={'rows': 4, 
                                                  'placeholder': 'Add notes, advice, or update for the reporter...'}),
        }


class HealthAdvisoryForm(forms.ModelForm):
    """Form for creating health advisories"""
    class Meta:
        model = HealthAdvisory
        fields = ['title', 'description', 'priority', 'region', 'related_cause', 
                  'preventive_measures', 'expires_at']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'preventive_measures': forms.Textarea(attrs={'rows': 4}),
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }