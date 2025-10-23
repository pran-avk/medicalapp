from django.conf import settings
from twilio.rest import Client
from celery import shared_task
from .models import Notification, NotificationTemplate
import logging

logger = logging.getLogger(__name__)

class TwilioService:
    """Service class for sending SMS and WhatsApp notifications via Twilio"""
    
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.phone_number = settings.TWILIO_PHONE_NUMBER
        self.client = None
        
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
    
    def send_sms(self, to_number, message, notification_id=None):
        """Send SMS message"""
        if not self.client:
            logger.error("Twilio client not initialized")
            return False
        
        try:
            # Format phone number
            if not to_number.startswith('+'):
                to_number = f'+91{to_number}'  # Assuming Indian numbers, adjust as needed
            
            message_instance = self.client.messages.create(
                body=message,
                from_=self.phone_number,
                to=to_number
            )
            
            logger.info(f"SMS sent successfully. SID: {message_instance.sid}")
            
            # Update notification status
            if notification_id:
                try:
                    notification = Notification.objects.get(id=notification_id)
                    notification.mark_as_sent()
                except Notification.DoesNotExist:
                    pass
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_number}: {e}")
            
            # Update notification status as failed
            if notification_id:
                try:
                    notification = Notification.objects.get(id=notification_id)
                    notification.mark_as_failed(str(e))
                except Notification.DoesNotExist:
                    pass
            
            return False
    
    def send_whatsapp(self, to_number, message, notification_id=None):
        """Send WhatsApp message"""
        if not self.client:
            logger.error("Twilio client not initialized")
            return False
        
        try:
            # Format phone number for WhatsApp
            if not to_number.startswith('+'):
                to_number = f'+91{to_number}'  # Assuming Indian numbers
            
            message_instance = self.client.messages.create(
                body=message,
                from_=f'whatsapp:{self.phone_number}',
                to=f'whatsapp:{to_number}'
            )
            
            logger.info(f"WhatsApp message sent successfully. SID: {message_instance.sid}")
            
            # Update notification status
            if notification_id:
                try:
                    notification = Notification.objects.get(id=notification_id)
                    notification.mark_as_sent()
                except Notification.DoesNotExist:
                    pass
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message to {to_number}: {e}")
            
            # Update notification status as failed
            if notification_id:
                try:
                    notification = Notification.objects.get(id=notification_id)
                    notification.mark_as_failed(str(e))
                except Notification.DoesNotExist:
                    pass
            
            return False

@shared_task(bind=True, max_retries=3)
def send_notification_task(self, notification_id):
    """Celery task to send notifications asynchronously"""
    try:
        notification = Notification.objects.get(id=notification_id)
        twilio_service = TwilioService()
        
        success = False
        
        if notification.channel == 'sms':
            success = twilio_service.send_sms(
                notification.recipient,
                notification.message,
                notification_id
            )
        elif notification.channel == 'whatsapp':
            success = twilio_service.send_whatsapp(
                notification.recipient,
                notification.message,
                notification_id
            )
        
        if not success and self.request.retries < self.max_retries:
            # Retry after 60 seconds
            raise self.retry(countdown=60)
        
        return success
        
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_id} not found")
        return False
    except Exception as e:
        logger.error(f"Error sending notification {notification_id}: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60)
        
        return False

@shared_task
def process_pending_notifications():
    """Process all pending notifications"""
    from django.utils import timezone
    
    pending_notifications = Notification.objects.filter(
        status='pending',
        scheduled_for__lte=timezone.now()
    )
    
    for notification in pending_notifications:
        send_notification_task.delay(notification.id)
    
    return f"Queued {pending_notifications.count()} notifications for sending"

def create_notification_templates():
    """Create default notification templates"""
    templates = [
        {
            'name': 'Token Issued',
            'template_type': 'token_issued',
            'sms_template': 'Hello {name}, your token number is {token_number} for {department}. Estimated wait time: {estimated_wait_time} minutes. SmartQueue',
            'whatsapp_template': 'Hello {name}, your token number is {token_number} for {department}. Estimated wait time: {estimated_wait_time} minutes. SmartQueue',
        },
        {
            'name': 'Turn Approaching',
            'template_type': 'turn_approaching',
            'sms_template': 'Hello {name}, your turn (Token #{token_number}) is approaching in {department}. Please be ready. SmartQueue',
            'whatsapp_template': 'Hello {name}, your turn (Token #{token_number}) is approaching in {department}. Please be ready. SmartQueue',
        },
        {
            'name': 'Turn Ready',
            'template_type': 'turn_ready',
            'sms_template': 'Hello {name}, your turn is ready! Please proceed to {department} for Token #{token_number}. SmartQueue',
            'whatsapp_template': 'Hello {name}, your turn is ready! Please proceed to {department} for Token #{token_number}. SmartQueue',
        },
        {
            'name': 'Missed Turn',
            'template_type': 'missed_turn',
            'sms_template': 'Hello {name}, you missed your turn for Token #{token_number} in {department}. Please contact reception. SmartQueue',
            'whatsapp_template': 'Hello {name}, you missed your turn for Token #{token_number} in {department}. Please contact reception. SmartQueue',
        },
        {
            'name': 'Consultation Complete',
            'template_type': 'consultation_complete',
            'sms_template': 'Hello {name}, your consultation for Token #{token_number} is complete. Thank you for visiting {department}. SmartQueue',
            'whatsapp_template': 'Hello {name}, your consultation for Token #{token_number} is complete. Thank you for visiting {department}. SmartQueue',
        },
    ]
    
    for template_data in templates:
        template, created = NotificationTemplate.objects.get_or_create(
            template_type=template_data['template_type'],
            defaults=template_data
        )
        if created:
            print(f"Created notification template: {template.name}")
        else:
            print(f"Notification template already exists: {template.name}")

# Management command to setup notification templates
def setup_notification_system():
    """Setup notification system with default templates"""
    create_notification_templates()
    print("Notification system setup complete!")