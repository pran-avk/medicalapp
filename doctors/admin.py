from django.contrib import admin
from .models import Doctor, DoctorSchedule, DoctorLeave

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['name', 'employee_id', 'specialization', 'department', 'is_available', 'is_active', 'total_patients_seen']
    list_filter = ['specialization', 'department', 'is_available', 'is_active', 'created_at']
    search_fields = ['name', 'employee_id', 'phone_number', 'email', 'license_number']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at', 'last_active', 'total_patients_seen']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'employee_id', 'phone_number', 'email')
        }),
        ('Professional Information', {
            'fields': ('specialization', 'license_number', 'years_of_experience', 'qualification')
        }),
        ('Department & Availability', {
            'fields': ('department', 'is_available', 'is_active')
        }),
        ('Schedule', {
            'fields': ('start_time', 'end_time', 'lunch_start', 'lunch_end')
        }),
        ('Statistics', {
            'fields': ('total_patients_seen', 'average_consultation_time'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_active'),
            'classes': ('collapse',)
        }),
    )

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'get_weekday_display', 'start_time', 'end_time', 'is_available']
    list_filter = ['weekday', 'is_available']
    search_fields = ['doctor__name']
    ordering = ['doctor', 'weekday']

@admin.register(DoctorLeave)
class DoctorLeaveAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'leave_type', 'start_date', 'end_date', 'is_approved', 'created_at']
    list_filter = ['leave_type', 'is_approved', 'start_date', 'created_at']
    search_fields = ['doctor__name', 'reason']
    ordering = ['-created_at']
    readonly_fields = ['created_at']
