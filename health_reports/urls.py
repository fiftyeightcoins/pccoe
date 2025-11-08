from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='health_reports/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # User paths
    path('submit-report/', views.submit_report, name='submit_report'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('report/<int:report_id>/', views.report_detail, name='report_detail'),
    
    # Admin paths
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('create-advisory/', views.create_advisory, name='create_advisory'),
    
    # Analytics
    path('analytics/', views.analytics_dashboard, name='analytics'),
    
    # API
    path('api/map-data/', views.api_map_data, name='api_map_data'),
    path('api/notification/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
]