from django.utils import timezone
from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Queue, Patient, Department
from notifications.models import Notification, NotificationTemplate, NotificationPreference

class QueueService:
    """Service class to handle queue operations and real-time updates"""
    
    def __init__(self):
        self.channel_layer = get_channel_layer()
    
    @transaction.atomic
    def register_patient(self, patient_data, department_id):
        """Register a new patient and assign token"""
        try:
            department = Department.objects.get(id=department_id, is_active=True)
            
            # Get or create patient
            patient, created = Patient.objects.get_or_create(
                phone_number=patient_data['phone_number'],
                defaults={
                    'name': patient_data['name'],
                    'email': patient_data.get('email', ''),
                    'age': patient_data.get('age'),
                    'gender': patient_data.get('gender', ''),
                    'address': patient_data.get('address', ''),
                    'emergency_contact': patient_data.get('emergency_contact', ''),
                }
            )
            
            # Check if patient already has a token for today
            existing_queue = patient.get_current_queue_entry()
            if existing_queue:
                return {
                    'success': False,
                    'message': 'Patient already has an active token for today',
                    'existing_token': existing_queue.token_number
                }
            
            # Create queue entry
            queue_entry = Queue.objects.create(
                patient=patient,
                department=department,
                priority=patient_data.get('priority', 'normal'),
                notes=patient_data.get('notes', '')
            )
            
            # Calculate estimated wait time
            queue_entry.calculate_estimated_wait_time()
            
            # Send notifications
            self.send_token_issued_notification(queue_entry)
            
            # Broadcast queue update
            self.broadcast_queue_update(department)
            
            return {
                'success': True,
                'token_number': queue_entry.token_number,
                'department': department.name,
                'estimated_wait_time': queue_entry.estimated_wait_time,
                'position': queue_entry.get_position_in_queue(),
                'queue_id': queue_entry.id
            }
            
        except Department.DoesNotExist:
            return {
                'success': False,
                'message': 'Department not found or inactive'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error registering patient: {str(e)}'
            }
    
    def call_next_patient(self, doctor):
        """Call next patient in queue for a doctor"""
        try:
            with transaction.atomic():
                next_patient = Queue.objects.filter(
                    department=doctor.department,
                    status='waiting',
                    created_at__date=timezone.now().date()
                ).order_by('priority', 'created_at').first()
                
                if not next_patient:
                    return {
                        'success': False,
                        'message': 'No patients waiting in queue'
                    }
                
                # Mark patient as called
                next_patient.mark_as_called()
                next_patient.assigned_doctor = doctor
                next_patient.save()
                
                # Send notifications
                self.send_turn_ready_notification(next_patient)
                
                # Update doctor statistics
                doctor.last_active = timezone.now()
                doctor.save()
                
                # Broadcast updates
                self.broadcast_queue_update(doctor.department)
                self.broadcast_patient_update(next_patient)
                
                return {
                    'success': True,
                    'patient': {
                        'id': next_patient.patient.id,
                        'name': next_patient.patient.name,
                        'phone': next_patient.patient.phone_number,
                        'token_number': next_patient.token_number,
                        'notes': next_patient.notes
                    }
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error calling patient: {str(e)}'
            }
    
    def start_consultation(self, queue_id, doctor):
        """Start consultation for a patient"""
        try:
            with transaction.atomic():
                queue_entry = Queue.objects.get(id=queue_id, assigned_doctor=doctor)
                queue_entry.start_consultation(doctor)
                
                # Update doctor statistics
                doctor.last_active = timezone.now()
                doctor.save()
                
                # Broadcast updates
                self.broadcast_queue_update(doctor.department)
                self.broadcast_patient_update(queue_entry)
                self.broadcast_doctor_update(doctor)
                
                return {
                    'success': True,
                    'message': 'Consultation started successfully'
                }
                
        except Queue.DoesNotExist:
            return {
                'success': False,
                'message': 'Queue entry not found or not assigned to this doctor'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error starting consultation: {str(e)}'
            }
    
    def complete_consultation(self, queue_id, doctor, notes=""):
        """Complete consultation for a patient"""
        try:
            with transaction.atomic():
                queue_entry = Queue.objects.get(id=queue_id, assigned_doctor=doctor)
                queue_entry.complete_consultation()
                if notes:
                    queue_entry.notes = notes
                    queue_entry.save()
                
                # Update doctor statistics
                doctor.total_patients_seen += 1
                doctor.last_active = timezone.now()
                doctor.save()
                
                # Send completion notification
                self.send_consultation_complete_notification(queue_entry)
                
                # Broadcast updates
                self.broadcast_queue_update(doctor.department)
                self.broadcast_patient_update(queue_entry)
                self.broadcast_doctor_update(doctor)
                
                return {
                    'success': True,
                    'message': 'Consultation completed successfully'
                }
                
        except Queue.DoesNotExist:
            return {
                'success': False,
                'message': 'Queue entry not found or not assigned to this doctor'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error completing consultation: {str(e)}'
            }
    
    def skip_patient(self, queue_id, reason=""):
        """Skip a patient (mark as late entry or skipped)"""
        try:
            with transaction.atomic():
                queue_entry = Queue.objects.get(id=queue_id)
                queue_entry.status = 'skipped'
                queue_entry.notes = f"Skipped: {reason}" if reason else "Skipped"
                queue_entry.save()
                
                # Send missed turn notification
                self.send_missed_turn_notification(queue_entry)
                
                # Broadcast updates
                self.broadcast_queue_update(queue_entry.department)
                self.broadcast_patient_update(queue_entry)
                
                return {
                    'success': True,
                    'message': 'Patient marked as skipped'
                }
                
        except Queue.DoesNotExist:
            return {
                'success': False,
                'message': 'Queue entry not found'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error skipping patient: {str(e)}'
            }
    
    def get_queue_status(self, department_id):
        """Get current queue status for a department"""
        try:
            department = Department.objects.get(id=department_id)
            today = timezone.now().date()
            
            waiting_queue = Queue.objects.filter(
                department=department,
                status='waiting',
                created_at__date=today
            ).order_by('created_at')
            
            in_consultation = Queue.objects.filter(
                department=department,
                status='in_consultation',
                created_at__date=today
            )
            
            completed_today = Queue.objects.filter(
                department=department,
                status='completed',
                created_at__date=today
            ).count()
            
            queue_data = []
            for i, queue_entry in enumerate(waiting_queue, 1):
                queue_data.append({
                    'id': queue_entry.id,
                    'token_number': queue_entry.token_number,
                    'patient_name': queue_entry.patient.name,
                    'patient_phone': queue_entry.patient.phone_number,
                    'estimated_wait_time': queue_entry.estimated_wait_time,
                    'position': i,
                    'priority': queue_entry.priority,
                    'created_at': queue_entry.created_at.isoformat(),
                })
            
            current_patients = []
            for queue_entry in in_consultation:
                current_patients.append({
                    'id': queue_entry.id,
                    'token_number': queue_entry.token_number,
                    'patient_name': queue_entry.patient.name,
                    'doctor_name': queue_entry.assigned_doctor.name if queue_entry.assigned_doctor else 'N/A',
                    'consultation_started_at': queue_entry.consultation_started_at.isoformat() if queue_entry.consultation_started_at else None,
                })
            
            return {
                'success': True,
                'department': department.name,
                'total_waiting': len(queue_data),
                'total_in_consultation': len(current_patients),
                'total_completed_today': completed_today,
                'waiting_queue': queue_data,
                'current_consultations': current_patients
            }
            
        except Department.DoesNotExist:
            return {
                'success': False,
                'message': 'Department not found'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error getting queue status: {str(e)}'
            }
    
    def get_patient_status(self, patient_id):
        """Get current status for a specific patient"""
        try:
            patient = Patient.objects.get(id=patient_id)
            queue_entry = patient.get_current_queue_entry()
            
            if not queue_entry:
                return {
                    'success': True,
                    'message': 'No active queue entry for today',
                    'has_active_token': False
                }
            
            return {
                'success': True,
                'has_active_token': True,
                'token_number': queue_entry.token_number,
                'department': queue_entry.department.name,
                'status': queue_entry.status,
                'position': queue_entry.get_position_in_queue(),
                'estimated_wait_time': queue_entry.estimated_wait_time,
                'created_at': queue_entry.created_at.isoformat(),
                'called_at': queue_entry.called_at.isoformat() if queue_entry.called_at else None,
                'consultation_started_at': queue_entry.consultation_started_at.isoformat() if queue_entry.consultation_started_at else None,
            }
            
        except Patient.DoesNotExist:
            return {
                'success': False,
                'message': 'Patient not found'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error getting patient status: {str(e)}'
            }
    
    # Notification methods
    def send_token_issued_notification(self, queue_entry):
        """Send notification when token is issued"""
        try:
            template = NotificationTemplate.objects.filter(
                template_type='token_issued',
                is_active=True
            ).first()
            
            if template:
                message = template.sms_template.format(
                    name=queue_entry.patient.name,
                    token_number=queue_entry.token_number,
                    department=queue_entry.department.name,
                    estimated_wait_time=queue_entry.estimated_wait_time or 'N/A'
                )
                
                Notification.objects.create(
                    patient=queue_entry.patient,
                    queue_entry=queue_entry,
                    channel='sms',
                    template=template,
                    message=message,
                    recipient=queue_entry.patient.phone_number
                )
        except Exception as e:
            print(f"Error sending token issued notification: {e}")
    
    def send_turn_ready_notification(self, queue_entry):
        """Send notification when patient's turn is ready"""
        try:
            template = NotificationTemplate.objects.filter(
                template_type='turn_ready',
                is_active=True
            ).first()
            
            if template:
                message = template.sms_template.format(
                    name=queue_entry.patient.name,
                    token_number=queue_entry.token_number,
                    department=queue_entry.department.name
                )
                
                Notification.objects.create(
                    patient=queue_entry.patient,
                    queue_entry=queue_entry,
                    channel='sms',
                    template=template,
                    message=message,
                    recipient=queue_entry.patient.phone_number
                )
        except Exception as e:
            print(f"Error sending turn ready notification: {e}")
    
    def send_missed_turn_notification(self, queue_entry):
        """Send notification when patient misses their turn"""
        try:
            template = NotificationTemplate.objects.filter(
                template_type='missed_turn',
                is_active=True
            ).first()
            
            if template:
                message = template.sms_template.format(
                    name=queue_entry.patient.name,
                    token_number=queue_entry.token_number,
                    department=queue_entry.department.name
                )
                
                Notification.objects.create(
                    patient=queue_entry.patient,
                    queue_entry=queue_entry,
                    channel='sms',
                    template=template,
                    message=message,
                    recipient=queue_entry.patient.phone_number
                )
        except Exception as e:
            print(f"Error sending missed turn notification: {e}")
    
    def send_consultation_complete_notification(self, queue_entry):
        """Send notification when consultation is complete"""
        try:
            template = NotificationTemplate.objects.filter(
                template_type='consultation_complete',
                is_active=True
            ).first()
            
            if template:
                message = template.sms_template.format(
                    name=queue_entry.patient.name,
                    token_number=queue_entry.token_number,
                    department=queue_entry.department.name
                )
                
                Notification.objects.create(
                    patient=queue_entry.patient,
                    queue_entry=queue_entry,
                    channel='sms',
                    template=template,
                    message=message,
                    recipient=queue_entry.patient.phone_number
                )
        except Exception as e:
            print(f"Error sending consultation complete notification: {e}")
    
    # WebSocket broadcast methods
    def broadcast_queue_update(self, department):
        """Broadcast queue update to all connected clients"""
        if self.channel_layer:
            async_to_sync(self.channel_layer.group_send)(
                f'queue_{department.id}',
                {
                    'type': 'queue_update',
                    'data': self.get_queue_status(department.id)
                }
            )
    
    def broadcast_patient_update(self, queue_entry):
        """Broadcast patient update to patient's WebSocket connection"""
        if self.channel_layer:
            async_to_sync(self.channel_layer.group_send)(
                f'patient_{queue_entry.patient.id}',
                {
                    'type': 'patient_update',
                    'data': {
                        'token_number': queue_entry.token_number,
                        'status': queue_entry.status,
                        'position': queue_entry.get_position_in_queue(),
                        'estimated_wait_time': queue_entry.estimated_wait_time,
                        'called_at': queue_entry.called_at.isoformat() if queue_entry.called_at else None,
                        'consultation_started_at': queue_entry.consultation_started_at.isoformat() if queue_entry.consultation_started_at else None,
                    }
                }
            )
    
    def broadcast_doctor_update(self, doctor):
        """Broadcast doctor update to doctor's WebSocket connection"""
        if self.channel_layer:
            current_patient = doctor.get_current_patient()
            next_patient = doctor.get_next_patient()
            
            async_to_sync(self.channel_layer.group_send)(
                f'doctor_{doctor.id}',
                {
                    'type': 'doctor_update',
                    'data': {
                        'waiting_count': doctor.get_waiting_patients_count(),
                        'today_patient_count': doctor.get_today_patient_count(),
                        'current_patient': {
                            'token_number': current_patient.token_number,
                            'name': current_patient.patient.name,
                            'phone': current_patient.patient.phone_number
                        } if current_patient else None,
                        'next_patient': {
                            'token_number': next_patient.token_number,
                            'name': next_patient.patient.name,
                            'phone': next_patient.patient.phone_number
                        } if next_patient else None,
                    }
                }
            )