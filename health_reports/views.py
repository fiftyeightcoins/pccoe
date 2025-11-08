from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import json
from .models import HealthAdvisory
from .models import HealthReport, Notification
from .forms import UserRegistrationForm, HealthReportForm, AdminReportReviewForm, HealthAdvisoryForm

def home(request):
    """Homepage with recent advisories"""
    advisories = HealthAdvisory.objects.filter(is_active=True)[:5]
    
    # Statistics
    total_reports = HealthReport.objects.count()
    resolved_reports = HealthReport.objects.filter(status='resolved').count()
    active_advisories = HealthAdvisory.objects.filter(is_active=True).count()
    
    context = {
        'advisories': advisories,
        'total_reports': total_reports,
        'resolved_reports': resolved_reports,
        'active_advisories': active_advisories,
    }
    return render(request, 'health_reports/home.html', context)


def register(request):
    """User registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to Climate Health Tracker.')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'health_reports/register.html', {'form': form})


@login_required
def submit_report(request):
    """Submit a new health report"""
    if request.method == 'POST':
        form = HealthReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.save()
            
            messages.success(request, 'Your report has been submitted successfully. You will be notified of any updates.')
            return redirect('user_dashboard')
    else:
        form = HealthReportForm()
    
    return render(request, 'health_reports/submit_report.html', {'form': form})


@login_required
def user_dashboard(request):
    """User dashboard showing their reports"""
    reports = HealthReport.objects.filter(reporter=request.user)
    notifications = Notification.objects.filter(user=request.user, is_read=False)[:5]
    
    context = {
        'reports': reports,
        'notifications': notifications,
    }
    return render(request, 'health_reports/user_dashboard.html', context)


@login_required
def admin_dashboard(request):
    """Admin dashboard for managing reports"""
    if not request.user.profile.is_admin():
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    # Filter options
    status_filter = request.GET.get('status', 'all')
    
    reports = HealthReport.objects.all()
    if status_filter != 'all':
        reports = reports.filter(status=status_filter)
    
    # Statistics
    pending_count = HealthReport.objects.filter(status='pending').count()
    verified_count = HealthReport.objects.filter(status='verified').count()
    resolved_count = HealthReport.objects.filter(status='resolved').count()
    
    context = {
        'reports': reports[:50],  # Limit to 50 for performance
        'pending_count': pending_count,
        'verified_count': verified_count,
        'resolved_count': resolved_count,
        'status_filter': status_filter,
    }
    return render(request, 'health_reports/admin_dashboard.html', context)


@login_required
def report_detail(request, report_id):
    """View and update report details"""
    report = get_object_or_404(HealthReport, id=report_id)
    
    # Check permissions
    if not (request.user == report.reporter or request.user.profile.is_admin()):
        messages.error(request, 'Access denied.')
        return redirect('home')
    
    if request.method == 'POST' and request.user.profile.is_admin():
        form = AdminReportReviewForm(request.POST, instance=report)
        if form.is_valid():
            updated_report = form.save(commit=False)
            old_status = report.status
            updated_report.verified_by = request.user
            updated_report.save()
            
            # Create notification for reporter
            if old_status != updated_report.status:
                Notification.objects.create(
                    user=report.reporter,
                    notification_type='report_update',
                    title=f'Report Status Updated: {updated_report.get_status_display()}',
                    message=f'Your report from {report.location} has been updated to {updated_report.get_status_display()}.',
                    related_report=updated_report
                )
                
                # Send email notification
                send_mail(
                    subject=f'Climate Health Tracker: Report Status Update',
                    message=f'Your report has been updated to {updated_report.get_status_display()}.\n\nAdmin Notes: {updated_report.admin_notes}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[report.reporter.email],
                    fail_silently=True,
                )
            
            messages.success(request, 'Report updated successfully.')
            return redirect('report_detail', report_id=report.id)
    else:
        form = AdminReportReviewForm(instance=report) if request.user.profile.is_admin() else None
    
    context = {
        'report': report,
        'form': form,
    }
    return render(request, 'health_reports/report_detail.html', context)


@login_required
def analytics_dashboard(request):
    """Analytics dashboard with charts and statistics"""
    # Disease type distribution
    disease_data = list(HealthReport.objects.values('disease_type').annotate(
        count=Count('id')
    ))
    
    # Environmental cause distribution
    cause_data = list(HealthReport.objects.values('environmental_cause').annotate(
        count=Count('id')
    ))
    
    # Status distribution
    status_data = list(HealthReport.objects.values('status').annotate(
        count=Count('id')
    ))
    
    # Reports over time (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    time_data = []
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        count = HealthReport.objects.filter(
            created_at__date=date.date()
        ).count()
        time_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    # Location-based data
    location_data = list(HealthReport.objects.values('location').annotate(
        count=Count('id')
    ).order_by('-count')[:10])
    
    context = {
        'disease_data': json.dumps(disease_data),
        'cause_data': json.dumps(cause_data),
        'status_data': json.dumps(status_data),
        'time_data': json.dumps(time_data),
        'location_data': json.dumps(location_data),
    }
    return render(request, 'health_reports/analytics.html', context)


@login_required
def create_advisory(request):
    """Create a new health advisory (admin only)"""
    if not request.user.profile.is_admin():
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('home')
    
    if request.method == 'POST':
        form = HealthAdvisoryForm(request.POST)
        if form.is_valid():
            advisory = form.save(commit=False)
            advisory.issued_by = request.user
            advisory.save()
            
            messages.success(request, 'Health advisory published successfully.')
            return redirect('admin_dashboard')
    else:
        form = HealthAdvisoryForm()
    
    return render(request, 'health_reports/create_advisory.html', {'form': form})


@login_required
def mark_notification_read(request, notification_id):
    """Mark notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})


# API endpoint for map data
@login_required
def api_map_data(request):
    """API endpoint for map visualization"""
    reports = HealthReport.objects.filter(
        latitude__isnull=False,
        longitude__isnull=False
    ).values('id', 'disease_type', 'location', 'latitude', 'longitude', 'status')
    
    return JsonResponse(list(reports), safe=False)