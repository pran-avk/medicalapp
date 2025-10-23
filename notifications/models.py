from django.db import models
from django.utils import timezone
from patients.models import Patient, Queue

class NotificationTemplate(models.Model):
    TEMPLATE_TYPES = [
        ('token_issued', 'Token Issued'),
        ('turn_approaching', 'Turn Approaching'),
        ('turn_ready', 'Turn Ready'),
        ('missed_turn', 'Missed Turn'),
        ('consultation_complete', 'Consultation Complete'),
        ('appointment_reminder', 'Appointment Reminder'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=30, choices=TEMPLATE_TYPES)
    sms_template = models.TextField(help_text="SMS template with placeholders like {name}, {token_number}, etc.")
    whatsapp_template = models.TextField(blank=True, help_text="WhatsApp template")
    email_template = models.TextField(blank=True, help_text="Email template")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_template_type_display()}"

class Notification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
    ]
    
    CHANNEL_CHOICES = [
        ('sms', 'SMS'),
        ('whatsapp', 'WhatsApp'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
    ]
    
    # Core Information
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    queue_entry = models.ForeignKey(Queue, on_delete=models.CASCADE, null=True, blank=True)
    
    # Message Information
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    message = models.TextField()
    recipient = models.CharField(max_length=100, help_text="Phone number, email, or device token")
    
    # Status Information
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Scheduling
    scheduled_for = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_channel_display()} to {self.patient.name} - {self.template.name}"
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.status = 'sent'
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])
    
    def mark_as_delivered(self):
        """Mark notification as delivered"""
        self.status = 'delivered'
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])
    
    def mark_as_failed(self, error_message=""):
        """Mark notification as failed"""
        self.status = 'failed'
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])

class NotificationPreference(models.Model):
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE)
    sms_enabled = models.BooleanField(default=True)
    whatsapp_enabled = models.BooleanField(default=False)
    email_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
    
    # Timing preferences
    notify_on_token_issue = models.BooleanField(default=True)
    notify_when_turn_approaches = models.BooleanField(default=True)
    notify_minutes_before = models.IntegerField(default=15, help_text="Minutes before turn to send notification")
    notify_on_turn_ready = models.BooleanField(default=True)
    notify_on_missed_turn = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Notification preferences for {self.patient.name}"
