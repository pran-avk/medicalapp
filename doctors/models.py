from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from patients.models import Department

class Doctor(models.Model):
    # Basic Information
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    
    # Professional Information
    specialization = models.CharField(max_length=100)
    license_number = models.CharField(max_length=50, unique=True)
    years_of_experience = models.IntegerField(default=0)
    qualification = models.CharField(max_length=200)
    
    # Department and Availability
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Schedule Information
    start_time = models.TimeField(default='09:00:00')
    end_time = models.TimeField(default='17:00:00')
    lunch_start = models.TimeField(default='13:00:00', null=True, blank=True)
    lunch_end = models.TimeField(default='14:00:00', null=True, blank=True)
    
    # Statistics
    total_patients_seen = models.IntegerField(default=0)
    average_consultation_time = models.IntegerField(default=15, help_text="Average time in minutes")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_active = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dr. {self.name} - {self.specialization}"
    
    def get_current_patient(self):
        """Get the current patient being consulted"""
        from patients.models import Queue
        return Queue.objects.filter(
            assigned_doctor=self,
            status='in_consultation',
            created_at__date=timezone.now().date()
        ).first()
    
    def get_next_patient(self):
        """Get the next patient in queue for this doctor"""
        from patients.models import Queue
        return Queue.objects.filter(
            department=self.department,
            status='waiting',
            created_at__date=timezone.now().date()
        ).order_by('priority', 'created_at').first()
    
    def get_waiting_patients_count(self):
        """Get count of patients waiting for this doctor's department"""
        from patients.models import Queue
        return Queue.objects.filter(
            department=self.department,
            status='waiting',
            created_at__date=timezone.now().date()
        ).count()
    
    def get_today_patient_count(self):
        """Get count of patients seen today"""
        from patients.models import Queue
        return Queue.objects.filter(
            assigned_doctor=self,
            status='completed',
            created_at__date=timezone.now().date()
        ).count()
    
    def is_on_duty(self):
        """Check if doctor is currently on duty"""
        now = timezone.now().time()
        if self.lunch_start and self.lunch_end:
            return (self.start_time <= now <= self.lunch_start) or (self.lunch_end <= now <= self.end_time)
        return self.start_time <= now <= self.end_time
    
    def call_next_patient(self):
        """Call the next patient in queue"""
        next_patient = self.get_next_patient()
        if next_patient:
            next_patient.mark_as_called()
            return next_patient
        return None

class DoctorSchedule(models.Model):
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='schedules')
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    lunch_start = models.TimeField(null=True, blank=True)
    lunch_end = models.TimeField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['doctor', 'weekday']
    
    def __str__(self):
        return f"{self.doctor.name} - {self.get_weekday_display()}"

class DoctorLeave(models.Model):
    LEAVE_TYPES = [
        ('sick', 'Sick Leave'),
        ('vacation', 'Vacation'),
        ('emergency', 'Emergency Leave'),
        ('conference', 'Conference/Training'),
        ('other', 'Other'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='leaves')
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.doctor.name} - {self.get_leave_type_display()} ({self.start_date} to {self.end_date})"
    
    def is_active_today(self):
        """Check if leave is active today"""
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date and self.is_approved
