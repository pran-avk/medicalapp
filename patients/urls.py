from django.urls import path
from . import views, booking_views

app_name = 'patients'

urlpatterns = [
    # API endpoints
    path('api/register/', views.PatientRegistrationView.as_view(), name='api_register'),
    path('api/departments/', views.get_departments, name='api_departments'),
    path('api/queue/<int:department_id>/', views.get_queue_status, name='api_queue_status'),
    path('api/patient/<int:patient_id>/status/', views.get_patient_status, name='api_patient_status'),
    path('api/check-patient/', views.check_patient_by_phone, name='api_check_patient'),
    path('api/feedback/', views.submit_feedback, name='api_feedback'),
    
    # Booking API endpoints
    path('api/booking/create/', booking_views.OnlineBookingView.as_view(), name='api_booking_create'),
    path('api/booking/<int:booking_id>/', booking_views.get_booking_details, name='api_booking_details'),
    path('api/booking/<int:booking_id>/cancel/', booking_views.cancel_booking, name='api_booking_cancel'),
    path('api/booking/qr-scan/', booking_views.QRScanView.as_view(), name='api_qr_scan'),
    path('api/booking/slots/<int:department_id>/', booking_views.get_available_slots, name='api_available_slots'),
    path('api/department/<int:department_id>/doctors/', booking_views.get_department_doctors, name='api_department_doctors'),
    
    # Template views
    path('register/', views.patient_registration, name='registration'),
    path('status/<int:patient_id>/', views.patient_status, name='status'),
    path('queue/<int:department_id>/', views.queue_display, name='queue_display'),
    path('feedback/<int:queue_id>/', views.feedback_form, name='feedback'),
    path('debug/', views.debug_page, name='debug'),
    
    # Booking template views
    path('booking/', booking_views.online_booking_page, name='booking'),
    path('booking/confirmation/<int:booking_id>/', booking_views.booking_confirmation_page, name='booking_confirmation'),
    path('qr-scanner/', booking_views.qr_scanner_page, name='qr_scanner'),
]