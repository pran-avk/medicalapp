"""
Doctor Registration Views
Allow new doctors to register and await admin approval
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
import json

from .models import Doctor, DoctorSchedule
from patients.models import Department
from adminpanel.models import AuditLog


class DoctorRegistrationView(View):
    """Handle doctor registration"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request):
        """Show registration form"""
        departments = Department.objects.filter(is_active=True)
        return render(request, 'doctors/register.html', {
            'departments': departments
        })
    
    def post(self, request):
        """Process registration"""
        try:
            data = json.loads(request.body)
            
            # Validate required fields
            required_fields = ['username', 'password', 'name', 'email', 'phone_number', 'department_id', 'specialization']
            for field in required_fields:
                if not data.get(field):
                    return JsonResponse({
                        'success': False,
                        'message': f'{field} is required'
                    }, status=400)
            
            # Check if username exists
            if User.objects.filter(username=data['username']).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Username already exists'
                }, status=400)
            
            # Check if email exists
            if User.objects.filter(email=data['email']).exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Email already registered'
                }, status=400)
            
            # Create user and doctor profile
            with transaction.atomic():
                # Create user account (inactive until approved)
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'],
                    first_name=data.get('name', '').split()[0] if data.get('name') else '',
                    last_name=' '.join(data.get('name', '').split()[1:]) if len(data.get('name', '').split()) > 1 else '',
                    is_active=False  # Needs admin approval
                )
                
                # Get department
                department = Department.objects.get(id=data['department_id'])
                
                # Create doctor profile
                doctor = Doctor.objects.create(
                    user=user,
                    name=data['name'],
                    specialization=data['specialization'],
                    department=department,
                    phone_number=data['phone_number'],
                    email=data['email'],
                    license_number=data.get('license_number', ''),
                    experience_years=data.get('experience_years', 0),
                    qualification=data.get('qualification', ''),
                    is_available=False,  # Will be set by admin after approval
                    total_patients_seen=0
                )
                
                # Log the registration
                AuditLog.log_action(
                    user=None,
                    action='doctor_registration',
                    description=f"New doctor registration: {data['name']} ({data['username']})",
                    model_name='Doctor',
                    object_id=doctor.id,
                    ip_address=self.get_client_ip(request)
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Registration successful! Your account is pending admin approval. You will receive an email once approved.',
                    'doctor_id': doctor.id
                }, status=201)
                
        except Department.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Department not found'
            }, status=400)
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


def pending_approval(request):
    """Page shown to doctors awaiting approval"""
    return render(request, 'doctors/pending_approval.html')


def check_username_availability(request):
    """API to check if username is available"""
    username = request.GET.get('username')
    if not username:
        return JsonResponse({'available': False, 'message': 'Username required'})
    
    available = not User.objects.filter(username=username).exists()
    return JsonResponse({
        'available': available,
        'message': 'Username available' if available else 'Username already taken'
    })
