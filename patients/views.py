from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import json

from .models import Patient, Department, Queue, PatientFeedback
from .services import QueueService
from adminpanel.models import AuditLog

class PatientRegistrationView(View):
    """Handle patient registration and token generation"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        try:
            # Parse request body
            data = json.loads(request.body)
            department_id = data.get('department_id')
            
            # Debug logging
            print(f"DEBUG - Registration data received: {data}")
            print(f"DEBUG - Department ID: {department_id}")
            
            # Validate required fields
            required_fields = ['name', 'phone_number']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False,
                        'message': f'{field} is required'
                    }, status=400)
            
            # Validate department_id
            if not department_id:
                return JsonResponse({
                    'success': False,
                    'message': 'Department is required'
                }, status=400)
            
            # Check if department exists
            try:
                from .models import Department
                dept = Department.objects.get(id=department_id, is_active=True)
                print(f"DEBUG - Found department: {dept.name}")
            except Department.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': f'Department with ID {department_id} not found or inactive'
                }, status=400)
            
            # Register patient using queue service
            queue_service = QueueService()
            result = queue_service.register_patient(data, department_id)
            
            # Log the action
            if result['success'] and request.user.is_authenticated:
                AuditLog.log_action(
                    user=request.user,
                    action='token_issue',
                    description=f"Token {result.get('token_number')} issued to {data['name']}",
                    model_name='Queue',
                    object_id=result.get('queue_id', ''),
                    ip_address=self.get_client_ip(request)
                )
            
            return JsonResponse(result, status=200 if result['success'] else 400)
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Server error: {str(e)}'
            }, status=500)
    
    def get_client_ip(self, request):
        """Get client's IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

@api_view(['GET'])
@permission_classes([AllowAny])
def get_departments(request):
    """Get list of active departments"""
    try:
        departments = Department.objects.filter(is_active=True)
        department_list = []
        
        for dept in departments:
            department_list.append({
                'id': dept.id,
                'name': dept.name,
                'description': dept.description,
                'waiting_count': dept.get_waiting_count(),
                'current_token': dept.get_current_token_number() - 1  # Last issued token
            })
        
        return Response({
            'success': True,
            'departments': department_list
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching departments: {str(e)}'
        }, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_queue_status(request, department_id):
    """Get queue status for a department"""
    try:
        queue_service = QueueService()
        result = queue_service.get_queue_status(department_id)
        return Response(result)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching queue status: {str(e)}'
        }, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_patient_status(request, patient_id):
    """Get patient's current queue status"""
    try:
        queue_service = QueueService()
        result = queue_service.get_patient_status(patient_id)
        return Response(result)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error fetching patient status: {str(e)}'
        }, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def check_patient_by_phone(request):
    """Check if patient exists by phone number"""
    try:
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({
                'success': False,
                'message': 'Phone number is required'
            }, status=400)
        
        try:
            patient = Patient.objects.get(phone_number=phone_number)
            queue_entry = patient.get_current_queue_entry()
            
            return Response({
                'success': True,
                'patient_exists': True,
                'patient': {
                    'id': patient.id,
                    'name': patient.name,
                    'phone_number': patient.phone_number,
                    'email': patient.email,
                },
                'has_active_token': bool(queue_entry),
                'queue_entry': {
                    'token_number': queue_entry.token_number,
                    'department': queue_entry.department.name,
                    'status': queue_entry.status,
                    'position': queue_entry.get_position_in_queue(),
                    'estimated_wait_time': queue_entry.estimated_wait_time
                } if queue_entry else None
            })
            
        except Patient.DoesNotExist:
            return Response({
                'success': True,
                'patient_exists': False,
                'has_active_token': False
            })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error checking patient: {str(e)}'
        }, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def submit_feedback(request):
    """Submit patient feedback after consultation"""
    try:
        data = request.data
        queue_id = data.get('queue_id')
        
        if not queue_id:
            return Response({
                'success': False,
                'message': 'Queue ID is required'
            }, status=400)
        
        try:
            queue_entry = Queue.objects.get(id=queue_id, status='completed')
            
            # Check if feedback already exists
            if hasattr(queue_entry, 'patientfeedback'):
                return Response({
                    'success': False,
                    'message': 'Feedback already submitted for this consultation'
                }, status=400)
            
            # Create feedback
            feedback = PatientFeedback.objects.create(
                queue_entry=queue_entry,
                rating=data.get('rating', 5),
                feedback_text=data.get('feedback_text', ''),
                wait_time_satisfaction=data.get('wait_time_satisfaction'),
                doctor_satisfaction=data.get('doctor_satisfaction'),
                overall_experience=data.get('overall_experience')
            )
            
            return Response({
                'success': True,
                'message': 'Feedback submitted successfully',
                'feedback_id': feedback.id
            })
            
        except Queue.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Queue entry not found or consultation not completed'
            }, status=404)
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error submitting feedback: {str(e)}'
        }, status=500)

# Template views for patient interface
def patient_registration(request):
    """Patient registration page"""
    departments = Department.objects.filter(is_active=True)
    return render(request, 'patients/registration.html', {
        'departments': departments
    })

def patient_status(request, patient_id):
    """Patient status page"""
    patient = get_object_or_404(Patient, id=patient_id)
    return render(request, 'patients/status.html', {
        'patient': patient
    })

def queue_display(request, department_id):
    """Public queue display for a department"""
    department = get_object_or_404(Department, id=department_id, is_active=True)
    return render(request, 'patients/queue_display.html', {
        'department': department
    })

def feedback_form(request, queue_id):
    """Feedback form after consultation"""
    queue_entry = get_object_or_404(Queue, id=queue_id, status='completed')
    return render(request, 'patients/feedback.html', {
        'queue_entry': queue_entry
    })

def debug_page(request):
    """Debug page for testing"""
    return render(request, 'patients/debug.html')
