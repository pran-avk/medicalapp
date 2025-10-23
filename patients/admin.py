from django.contrib import admin
from .models import Patient, Department, Queue, PatientFeedback

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at', 'get_waiting_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    
    def get_waiting_count(self, obj):
        return obj.get_waiting_count()
    get_waiting_count.short_description = 'Current Waiting'

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone_number', 'email', 'age', 'gender', 'created_at', 'is_active']
    list_filter = ['gender', 'is_active', 'created_at']
    search_fields = ['name', 'phone_number', 'email', 'medical_record_number']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
    list_display = ['token_number', 'patient', 'department', 'status', 'priority', 'created_at', 'assigned_doctor']
    list_filter = ['status', 'priority', 'department', 'created_at']
    search_fields = ['patient__name', 'patient__phone_number', 'token_number']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'actual_wait_time']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('patient', 'department', 'assigned_doctor')

@admin.register(PatientFeedback)
class PatientFeedbackAdmin(admin.ModelAdmin):
    list_display = ['queue_entry', 'rating', 'wait_time_satisfaction', 'doctor_satisfaction', 'created_at']
    list_filter = ['rating', 'wait_time_satisfaction', 'doctor_satisfaction', 'created_at']
    search_fields = ['queue_entry__patient__name', 'feedback_text']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
