from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from patients.models import Department, Queue
from doctors.models import Doctor

class AdminUser(models.Model):
    ROLE_CHOICES = [
        ('super_admin', 'Super Administrator'),
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')
    departments = models.ManyToManyField(Department, blank=True, help_text="Departments this admin can manage")
    phone_number = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def can_manage_department(self, department):
        """Check if admin can manage a specific department"""
        return self.role in ['super_admin', 'admin'] or department in self.departments.all()

class DepartmentAnalytics(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    
    # Patient Statistics
    total_patients = models.IntegerField(default=0)
    total_completed = models.IntegerField(default=0)
    total_cancelled = models.IntegerField(default=0)
    total_missed = models.IntegerField(default=0)
    
    # Timing Statistics
    average_wait_time = models.FloatField(default=0.0, help_text="Average wait time in minutes")
    average_consultation_time = models.FloatField(default=0.0, help_text="Average consultation time in minutes")
    peak_hour_start = models.TimeField(null=True, blank=True)
    peak_hour_end = models.TimeField(null=True, blank=True)
    
    # Efficiency Metrics
    patient_satisfaction_avg = models.FloatField(default=0.0, help_text="Average satisfaction rating")
    doctors_on_duty = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['department', 'date']
    
    def __str__(self):
        return f"{self.department.name} - {self.date}"
    
    @classmethod
    def generate_daily_analytics(cls, date=None):
        """Generate analytics for all departments for a specific date"""
        if not date:
            date = timezone.now().date()
        
        for department in Department.objects.filter(is_active=True):
            analytics, created = cls.objects.get_or_create(
                department=department,
                date=date,
                defaults={
                    'total_patients': 0,
                    'total_completed': 0,
                    'total_cancelled': 0,
                    'total_missed': 0,
                    'average_wait_time': 0.0,
                    'average_consultation_time': 0.0,
                    'patient_satisfaction_avg': 0.0,
                    'doctors_on_duty': 0,
                }
            )
            
            # Calculate statistics
            queues = Queue.objects.filter(
                department=department,
                created_at__date=date
            )
            
            analytics.total_patients = queues.count()
            analytics.total_completed = queues.filter(status='completed').count()
            analytics.total_cancelled = queues.filter(status='cancelled').count()
            analytics.total_missed = queues.filter(status='skipped').count()
            
            # Calculate average wait time
            completed_queues = queues.filter(status='completed', actual_wait_time__isnull=False)
            if completed_queues.exists():
                analytics.average_wait_time = completed_queues.aggregate(
                    avg_wait=models.Avg('actual_wait_time')
                )['avg_wait'] or 0.0
            
            # Calculate average consultation time
            consultation_times = []
            for queue in completed_queues:
                if queue.consultation_started_at and queue.consultation_ended_at:
                    duration = (queue.consultation_ended_at - queue.consultation_started_at).total_seconds() / 60
                    consultation_times.append(duration)
            
            if consultation_times:
                analytics.average_consultation_time = sum(consultation_times) / len(consultation_times)
            
            # Count doctors on duty
            analytics.doctors_on_duty = Doctor.objects.filter(
                department=department,
                is_available=True,
                is_active=True
            ).count()
            
            # Calculate patient satisfaction
            from patients.models import PatientFeedback
            feedbacks = PatientFeedback.objects.filter(
                queue_entry__department=department,
                queue_entry__created_at__date=date
            )
            if feedbacks.exists():
                analytics.patient_satisfaction_avg = feedbacks.aggregate(
                    avg_rating=models.Avg('rating')
                )['avg_rating'] or 0.0
            
            analytics.save()

class SystemConfiguration(models.Model):
    CONFIG_TYPES = [
        ('general', 'General Settings'),
        ('notification', 'Notification Settings'),
        ('queue', 'Queue Settings'),
        ('analytics', 'Analytics Settings'),
    ]
    
    config_type = models.CharField(max_length=20, choices=CONFIG_TYPES)
    key = models.CharField(max_length=100)
    value = models.TextField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['config_type', 'key']
    
    def __str__(self):
        return f"{self.get_config_type_display()} - {self.key}"
    
    @classmethod
    def get_config(cls, config_type, key, default=None):
        """Get configuration value"""
        try:
            config = cls.objects.get(config_type=config_type, key=key, is_active=True)
            return config.value
        except cls.DoesNotExist:
            return default
    
    @classmethod
    def set_config(cls, config_type, key, value, description=""):
        """Set configuration value"""
        config, created = cls.objects.update_or_create(
            config_type=config_type,
            key=key,
            defaults={
                'value': value,
                'description': description,
                'is_active': True
            }
        )
        return config

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('queue_manage', 'Queue Management'),
        ('token_issue', 'Token Issue'),
        ('patient_call', 'Patient Call'),
        ('consultation_start', 'Consultation Start'),
        ('consultation_end', 'Consultation End'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50, blank=True)
    object_id = models.CharField(max_length=50, blank=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} at {self.timestamp}"
    
    @classmethod
    def log_action(cls, user, action, description, model_name="", object_id="", ip_address=None, user_agent=""):
        """Create audit log entry"""
        return cls.objects.create(
            user=user,
            action=action,
            model_name=model_name,
            object_id=str(object_id) if object_id else "",
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )
