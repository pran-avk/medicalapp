from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import json

from .models import Doctor, DoctorSchedule
from patients.models import Queue, Department
from patients.services import QueueService
from adminpanel.models import AuditLog

@login_required
def doctor_dashboard(request):
    """Main doctor dashboard"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return redirect('admin:login')
    
    # Get today's statistics
    today = timezone.now().date()
    waiting_patients = Queue.objects.filter(
        department=doctor.department,
        status='waiting',
        created_at__date=today
    ).order_by('priority', 'created_at')
    
    # Get in-progress consultations
    in_progress = Queue.objects.filter(
        department=doctor.department,
        status='in_consultation',
        created_at__date=today
    ).count()
    
    # Get completed today
    completed_today = Queue.objects.filter(
        department=doctor.department,
        status='completed',
        created_at__date=today
    ).count()
    
    current_patient = doctor.get_current_patient()
    
    # Get today's schedule
    current_weekday = timezone.now().weekday()
    schedule = DoctorSchedule.objects.filter(
        doctor=doctor,
        weekday=current_weekday
    ).first()
    
    context = {
        'doctor': doctor,
        'waiting_count': waiting_patients.count(),
        'today_total': waiting_patients.count() + in_progress + completed_today,
        'in_progress': in_progress,
        'completed_count': completed_today,
        'schedule': schedule,
    }
    
    return render(request, 'doctors/dashboard.html', context)

@login_required
def doctor_schedule(request):
    """Doctor schedule management"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return redirect('admin:login')
    
    schedules = DoctorSchedule.objects.filter(doctor=doctor).order_by('weekday')
    
    context = {
        'doctor': doctor,
        'schedules': schedules,
    }
    
    return render(request, 'doctors/schedule.html', context)

@login_required
def patient_history(request):
    """Patient consultation history"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return redirect('admin:login')
    
    # Get recent consultations
    recent_consultations = Queue.objects.filter(
        assigned_doctor=doctor,
        status='completed'
    ).order_by('-consultation_ended_at')[:50]
    
    context = {
        'doctor': doctor,
        'consultations': recent_consultations,
    }
    
    return render(request, 'doctors/history.html', context)

class DoctorApiView(View):
    """API views for doctor operations"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
        
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Doctor profile not found'}, status=404)
        
        try:
            data = json.loads(request.body)
            action = data.get('action')
            queue_service = QueueService()
            
            if action == 'call_next':
                result = queue_service.call_next_patient(doctor)
                
                # Log the action
                if result['success']:
                    AuditLog.log_action(
                        user=request.user,
                        action='patient_call',
                        description=f"Called next patient: Token {result['patient']['token_number']}",
                        model_name='Queue',
                        ip_address=self.get_client_ip(request)
                    )
                
                return JsonResponse(result)
            
            elif action == 'start_consultation':
                queue_id = data.get('queue_id')
                if not queue_id:
                    return JsonResponse({'success': False, 'message': 'Queue ID required'})
                
                result = queue_service.start_consultation(queue_id, doctor)
                
                # Log the action
                if result['success']:
                    AuditLog.log_action(
                        user=request.user,
                        action='consultation_start',
                        description=f"Started consultation for queue ID {queue_id}",
                        model_name='Queue',
                        object_id=queue_id,
                        ip_address=self.get_client_ip(request)
                    )
                
                return JsonResponse(result)
            
            elif action == 'complete_consultation':
                queue_id = data.get('queue_id')
                notes = data.get('notes', '')
                
                if not queue_id:
                    return JsonResponse({'success': False, 'message': 'Queue ID required'})
                
                result = queue_service.complete_consultation(queue_id, doctor, notes)
                
                # Log the action
                if result['success']:
                    AuditLog.log_action(
                        user=request.user,
                        action='consultation_end',
                        description=f"Completed consultation for queue ID {queue_id}",
                        model_name='Queue',
                        object_id=queue_id,
                        ip_address=self.get_client_ip(request)
                    )
                
                return JsonResponse(result)
            
            elif action == 'skip_patient':
                queue_id = data.get('queue_id')
                reason = data.get('reason', '')
                
                if not queue_id:
                    return JsonResponse({'success': False, 'message': 'Queue ID required'})
                
                result = queue_service.skip_patient(queue_id, reason)
                
                # Log the action
                if result['success']:
                    AuditLog.log_action(
                        user=request.user,
                        action='queue_manage',
                        description=f"Skipped patient: Queue ID {queue_id}, Reason: {reason}",
                        model_name='Queue',
                        object_id=queue_id,
                        ip_address=self.get_client_ip(request)
                    )
                
                return JsonResponse(result)
            
            elif action == 'update_availability':
                is_available = data.get('is_available', True)
                doctor.is_available = is_available
                doctor.save()
                
                # Log the action
                AuditLog.log_action(
                    user=request.user,
                    action='update',
                    description=f"Updated availability to {'Available' if is_available else 'Unavailable'}",
                    model_name='Doctor',
                    object_id=doctor.id,
                    ip_address=self.get_client_ip(request)
                )
                
                return JsonResponse({
                    'success': True,
                    'message': f'Availability updated to {"Available" if is_available else "Unavailable"}'
                })
            
            else:
                return JsonResponse({'success': False, 'message': 'Invalid action'})
        
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Server error: {str(e)}'}, status=500)
    
    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Authentication required'}, status=401)
        
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Doctor profile not found'}, status=404)
        
        # Get current statistics
        today = timezone.now().date()
        waiting_patients = Queue.objects.filter(
            department=doctor.department,
            status='waiting',
            created_at__date=today
        ).order_by('priority', 'created_at')
        
        in_progress_count = Queue.objects.filter(
            department=doctor.department,
            status='in_consultation',
            created_at__date=today
        ).count()
        
        completed_count = Queue.objects.filter(
            department=doctor.department,
            status='completed',
            created_at__date=today
        ).count()
        
        current_patient = doctor.get_current_patient()
        
        waiting_list = []
        for queue_entry in waiting_patients:
            waiting_list.append({
                'id': queue_entry.id,
                'token_number': queue_entry.token_number,
                'patient_name': queue_entry.patient.name,
                'patient_phone': queue_entry.patient.phone_number,
                'phone_number': queue_entry.patient.phone_number,
                'age': queue_entry.patient.age,
                'priority': queue_entry.priority,
                'notes': queue_entry.notes,
                'created_at': queue_entry.created_at.isoformat(),
                'estimated_wait_time': queue_entry.estimated_wait_time,
                'position': queue_entry.get_position_in_queue(),
            })
        
        return JsonResponse({
            'success': True,
            'doctor': {
                'id': doctor.id,
                'name': doctor.name,
                'specialization': doctor.specialization,
                'department': doctor.department.name,
                'is_available': doctor.is_available,
                'is_on_duty': doctor.is_on_duty(),
            },
            'statistics': {
                'waiting_count': waiting_patients.count(),
                'today_completed': completed_count,
                'in_progress': in_progress_count,
                'today_total': waiting_patients.count() + in_progress_count + completed_count,
                'total_patients_seen': doctor.total_patients_seen,
            },
            'current_patient': {
                'id': current_patient.id,
                'token_number': current_patient.token_number,
                'patient_name': current_patient.patient.name,
                'patient_phone': current_patient.patient.phone_number,
                'age': current_patient.patient.age,
                'priority': current_patient.priority,
                'notes': current_patient.notes,
                'status': current_patient.status,
                'consultation_started_at': current_patient.consultation_started_at.isoformat() if current_patient.consultation_started_at else None,
            } if current_patient else None,
            'waiting_list': waiting_list,
        })
    
    def get_client_ip(self, request):
        """Get client's IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_schedule(request):
    """Update doctor schedule"""
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return Response({'success': False, 'message': 'Doctor profile not found'}, status=404)
    
    try:
        schedule_data = request.data.get('schedules', [])
        
        for schedule_item in schedule_data:
            weekday = schedule_item.get('weekday')
            start_time = schedule_item.get('start_time')
            end_time = schedule_item.get('end_time')
            is_available = schedule_item.get('is_available', True)
            lunch_start = schedule_item.get('lunch_start')
            lunch_end = schedule_item.get('lunch_end')
            
            if weekday is not None:
                schedule, created = DoctorSchedule.objects.update_or_create(
                    doctor=doctor,
                    weekday=weekday,
                    defaults={
                        'start_time': start_time,
                        'end_time': end_time,
                        'lunch_start': lunch_start,
                        'lunch_end': lunch_end,
                        'is_available': is_available,
                    }
                )
        
        # Log the action
        AuditLog.log_action(
            user=request.user,
            action='update',
            description="Updated doctor schedule",
            model_name='DoctorSchedule',
            object_id=doctor.id
        )
        
        return Response({
            'success': True,
            'message': 'Schedule updated successfully'
        })
        
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Error updating schedule: {str(e)}'
        }, status=500)

def doctor_login(request):
    """Doctor login page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                doctor = Doctor.objects.get(user=user)
                login(request, user)
                
                # Log the action
                AuditLog.log_action(
                    user=user,
                    action='login',
                    description="Doctor logged in",
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                return redirect('doctors:dashboard')
            except Doctor.DoesNotExist:
                return render(request, 'doctors/login.html', {
                    'error': 'User is not registered as a doctor'
                })
        else:
            return render(request, 'doctors/login.html', {
                'error': 'Invalid username or password'
            })
    
    return render(request, 'doctors/login.html')

@login_required
def doctor_logout(request):
    """Doctor logout"""
    # Log the action
    AuditLog.log_action(
        user=request.user,
        action='logout',
        description="Doctor logged out",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    logout(request)
    return redirect('doctors:login')
