from django.urls import path
from . import views, registration_views

app_name = 'doctors'

urlpatterns = [
    # Authentication
    path('login/', views.doctor_login, name='login'),
    path('logout/', views.doctor_logout, name='logout'),
    
    # Registration
    path('register/', registration_views.DoctorRegistrationView.as_view(), name='register'),
    path('pending-approval/', registration_views.pending_approval, name='pending_approval'),
    path('api/check-username/', registration_views.check_username_availability, name='check_username'),
    
    # Dashboard views
    path('dashboard/', views.doctor_dashboard, name='dashboard'),
    path('schedule/', views.doctor_schedule, name='schedule'),
    path('history/', views.patient_history, name='history'),
    
    # API endpoints
    path('api/', views.DoctorApiView.as_view(), name='api'),
    path('api/schedule/', views.update_schedule, name='api_schedule'),
]