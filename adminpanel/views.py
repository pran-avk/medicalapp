from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta
import json

from .models import AdminUser, DepartmentAnalytics, SystemConfiguration, AuditLog
from patients.models import Department, Queue, Patient, PatientFeedback
from doctors.models import Doctor
from notifications.models import Notification, NotificationTemplate

def is_admin(user):
    """Check if user is an admin"""
    try:
        admin_user = AdminUser.objects.get(user=user)
        return admin_user.role in ['super_admin', 'admin', 'manager']
    except AdminUser.DoesNotExist:
        return False

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Main admin dashboard"""
    try:
        admin_user = AdminUser.objects.get(user=request.user)
    except AdminUser.DoesNotExist:
        return redirect('admin:login')
    
    today = timezone.now().date()
    
    # Get overall statistics
    total_departments = Department.objects.filter(is_active=True).count()
    total_doctors = Doctor.objects.filter(is_active=True).count()
    total_patients_today = Queue.objects.filter(created_at__date=today).count()
    active_queues = Queue.objects.filter(
        status__in=['waiting', 'called', 'in_consultation'],
        created_at__date=today
    ).count()
    
    # Get department-wise statistics
    department_stats = []
    departments = Department.objects.filter(is_active=True)
    
    for dept in departments:
        if admin_user.can_manage_department(dept):
            stats = {
                'department': dept,
                'waiting_count': dept.get_waiting_count(),
                'today_total': Queue.objects.filter(
                    department=dept,
                    created_at__date=today
                ).count(),
                'completed_today': Queue.objects.filter(
                    department=dept,
                    status='completed',
                    created_at__date=today
                ).count(),
                'doctors_on_duty': Doctor.objects.filter(
                    department=dept,
                    is_available=True,
                    is_active=True
                ).count(),
            }
            department_stats.append(stats)
    
    # Get recent activities
    recent_activities = AuditLog.objects.filter(
        timestamp__date=today
    ).order_by('-timestamp')[:20]
    
    context = {
        'admin_user': admin_user,
        'total_departments': total_departments,
        'total_doctors': total_doctors,
        'total_patients_today': total_patients_today,
        'active_queues': active_queues,
        'department_stats': department_stats,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'adminpanel/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def departments_management(request):
    """Department management page"""
    try:
        admin_user = AdminUser.objects.get(user=request.user)
    except AdminUser.DoesNotExist:
        return redirect('admin:login')
    
    if admin_user.role in ['super_admin', 'admin']:
        departments = Department.objects.all()
    else:
        departments = admin_user.departments.all()
    
    context = {
        'admin_user': admin_user,
        'departments': departments,
    }
    
    return render(request, 'adminpanel/departments.html', context)

@login_required
@user_passes_test(is_admin)
def doctors_management(request):
    """Doctor management page"""
    try:
        admin_user = AdminUser.objects.get(user=request.user)
    except AdminUser.DoesNotExist:
        return redirect('admin:login')
    
    if admin_user.role in ['super_admin', 'admin']:
        doctors = Doctor.objects.all()
    else:
        doctors = Doctor.objects.filter(department__in=admin_user.departments.all())
    
    context = {
        'admin_user': admin_user,
        'doctors': doctors,
    }
    
    return render(request, 'adminpanel/doctors.html', context)

@login_required
@user_passes_test(is_admin)
def analytics_dashboard(request):
    """Analytics and reports dashboard"""
    try:
        admin_user = AdminUser.objects.get(user=request.user)
    except AdminUser.DoesNotExist:
        return redirect('admin:login')
    
    # Get date range from request
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)  # Default to last 30 days
    
    if request.GET.get('start_date'):
        start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d').date()
    if request.GET.get('end_date'):
        end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d').date()
    
    # Get analytics data
    analytics_data = []
    departments = admin_user.departments.all() if admin_user.role not in ['super_admin', 'admin'] else Department.objects.filter(is_active=True)
    
    for dept in departments:
        dept_analytics = DepartmentAnalytics.objects.filter(
            department=dept,
            date__range=[start_date, end_date]
        )
        
        if dept_analytics.exists():
            analytics = {
                'department': dept,
                'total_patients': dept_analytics.aggregate(total=Count('total_patients'))['total'] or 0,
                'avg_wait_time': dept_analytics.aggregate(avg=Avg('average_wait_time'))['avg'] or 0,
                'avg_consultation_time': dept_analytics.aggregate(avg=Avg('average_consultation_time'))['avg'] or 0,
                'satisfaction_avg': dept_analytics.aggregate(avg=Avg('patient_satisfaction_avg'))['avg'] or 0,
                'completion_rate': 0,  # Calculate completion rate
            }
            
            # Calculate completion rate
            total = dept_analytics.aggregate(total=Count('total_patients'))['total'] or 0
            completed = dept_analytics.aggregate(completed=Count('total_completed'))['completed'] or 0
            if total > 0:
                analytics['completion_rate'] = (completed / total) * 100
            
            analytics_data.append(analytics)
    
    # Get recent feedback
    recent_feedback = PatientFeedback.objects.filter(
        created_at__date__range=[start_date, end_date]
    ).order_by('-created_at')[:10]
    
    context = {
        'admin_user': admin_user,
        'analytics_data': analytics_data,
        'recent_feedback': recent_feedback,
        'start_date': start_date,
        'end_date': end_date,
    }
    
    return render(request, 'adminpanel/analytics.html', context)

@login_required
@user_passes_test(is_admin)
def queue_management(request):
    """Live queue management"""
    try:
        admin_user = AdminUser.objects.get(user=request.user)
    except AdminUser.DoesNotExist:
        return redirect('admin:login')
    
    today = timezone.now().date()
    departments = admin_user.departments.all() if admin_user.role not in ['super_admin', 'admin'] else Department.objects.filter(is_active=True)
    
    # Get current queues for all managed departments
    current_queues = {}
    for dept in departments:
        queues = Queue.objects.filter(
            department=dept,
            created_at__date=today,
            status__in=['waiting', 'called', 'in_consultation']
        ).order_by('created_at')
        current_queues[dept] = queues
    
    context = {
        'admin_user': admin_user,
        'current_queues': current_queues,
        'departments': departments,
    }
    
    return render(request, 'adminpanel/queue_management.html', context)

@login_required
@user_passes_test(is_admin)
def notifications_management(request):
    """Notification management"""
    try:
        admin_user = AdminUser.objects.get(user=request.user)
    except AdminUser.DoesNotExist:
        return redirect('admin:login')
    
    # Get notification templates
    templates = NotificationTemplate.objects.all()
    
    # Get recent notifications
    recent_notifications = Notification.objects.order_by('-created_at')[:50]
    
    # Get notification statistics
    notification_stats = {
        'total_sent': Notification.objects.filter(status='sent').count(),
        'pending': Notification.objects.filter(status='pending').count(),
        'failed': Notification.objects.filter(status='failed').count(),
    }
    
    context = {
        'admin_user': admin_user,
        'templates': templates,
        'recent_notifications': recent_notifications,
        'notification_stats': notification_stats,
    }
    
    return render(request, 'adminpanel/notifications.html', context)

class AdminApiView(View):
    """API views for admin operations"""
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request):
        if not request.user.is_authenticated or not is_admin(request.user):
            return JsonResponse({'success': False, 'message': 'Admin access required'}, status=401)
        
        try:
            admin_user = AdminUser.objects.get(user=request.user)
        except AdminUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Admin profile not found'}, status=404)
        
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            if action == 'create_department':
                name = data.get('name')
                description = data.get('description', '')
                
                if not name:
                    return JsonResponse({'success': False, 'message': 'Department name is required'})
                
                department = Department.objects.create(
                    name=name,
                    description=description
                )
                
                # Log the action
                AuditLog.log_action(
                    user=request.user,
                    action='create',
                    description=f"Created department: {name}",
                    model_name='Department',
                    object_id=department.id,
                    ip_address=self.get_client_ip(request)
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Department created successfully',
                    'department_id': department.id
                })
            
            elif action == 'update_department':
                dept_id = data.get('department_id')
                name = data.get('name')
                description = data.get('description', '')
                is_active = data.get('is_active', True)
                
                if not dept_id or not name:
                    return JsonResponse({'success': False, 'message': 'Department ID and name are required'})
                
                try:
                    department = Department.objects.get(id=dept_id)
                    
                    # Check permissions
                    if not admin_user.can_manage_department(department):
                        return JsonResponse({'success': False, 'message': 'No permission to manage this department'})
                    
                    department.name = name
                    department.description = description
                    department.is_active = is_active
                    department.save()
                    
                    # Log the action
                    AuditLog.log_action(
                        user=request.user,
                        action='update',
                        description=f"Updated department: {name}",
                        model_name='Department',
                        object_id=department.id,
                        ip_address=self.get_client_ip(request)
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Department updated successfully'
                    })
                    
                except Department.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Department not found'})
            
            elif action == 'generate_analytics':
                date_str = data.get('date')
                if date_str:
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                else:
                    date = timezone.now().date()
                
                DepartmentAnalytics.generate_daily_analytics(date)
                
                return JsonResponse({
                    'success': True,
                    'message': f'Analytics generated for {date}'
                })
            
            elif action == 'manage_queue':
                queue_id = data.get('queue_id')
                new_status = data.get('status')
                reason = data.get('reason', '')
                
                if not queue_id or not new_status:
                    return JsonResponse({'success': False, 'message': 'Queue ID and status are required'})
                
                try:
                    queue_entry = Queue.objects.get(id=queue_id)
                    
                    # Check permissions
                    if not admin_user.can_manage_department(queue_entry.department):
                        return JsonResponse({'success': False, 'message': 'No permission to manage this queue'})
                    
                    old_status = queue_entry.status
                    queue_entry.status = new_status
                    if reason:
                        queue_entry.notes = f"{queue_entry.notes}\nAdmin action: {reason}".strip()
                    queue_entry.save()
                    
                    # Log the action
                    AuditLog.log_action(
                        user=request.user,
                        action='queue_manage',
                        description=f"Changed queue status from {old_status} to {new_status}. Reason: {reason}",
                        model_name='Queue',
                        object_id=queue_entry.id,
                        ip_address=self.get_client_ip(request)
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'message': 'Queue status updated successfully'
                    })
                    
                except Queue.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Queue entry not found'})
            
            else:
                return JsonResponse({'success': False, 'message': 'Invalid action'})
        
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Server error: {str(e)}'}, status=500)
    
    def get(self, request):
        if not request.user.is_authenticated or not is_admin(request.user):
            return JsonResponse({'success': False, 'message': 'Admin access required'}, status=401)
        
        try:
            admin_user = AdminUser.objects.get(user=request.user)
        except AdminUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Admin profile not found'}, status=404)
        
        # Get dashboard statistics
        today = timezone.now().date()
        
        # Get system-wide statistics
        system_stats = {
            'total_departments': Department.objects.filter(is_active=True).count(),
            'total_doctors': Doctor.objects.filter(is_active=True).count(),
            'total_patients_today': Queue.objects.filter(created_at__date=today).count(),
            'active_queues': Queue.objects.filter(
                status__in=['waiting', 'called', 'in_consultation'],
                created_at__date=today
            ).count(),
            'notifications_pending': Notification.objects.filter(status='pending').count(),
        }
        
        # Get department statistics
        departments = admin_user.departments.all() if admin_user.role not in ['super_admin', 'admin'] else Department.objects.filter(is_active=True)
        department_stats = []
        
        for dept in departments:
            stats = {
                'id': dept.id,
                'name': dept.name,
                'waiting_count': dept.get_waiting_count(),
                'today_total': Queue.objects.filter(
                    department=dept,
                    created_at__date=today
                ).count(),
                'completed_today': Queue.objects.filter(
                    department=dept,
                    status='completed',
                    created_at__date=today
                ).count(),
                'doctors_on_duty': Doctor.objects.filter(
                    department=dept,
                    is_available=True,
                    is_active=True
                ).count(),
            }
            department_stats.append(stats)
        
        return JsonResponse({
            'success': True,
            'admin_user': {
                'username': admin_user.user.username,
                'role': admin_user.role,
                'can_manage_all': admin_user.role in ['super_admin', 'admin'],
            },
            'system_stats': system_stats,
            'department_stats': department_stats,
        })
    
    def get_client_ip(self, request):
        """Get client's IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

def admin_login(request):
    """Admin login page"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                admin_user = AdminUser.objects.get(user=user)
                if admin_user.is_active:
                    login(request, user)
                    
                    # Log the action
                    AuditLog.log_action(
                        user=user,
                        action='login',
                        description="Admin logged in",
                        ip_address=request.META.get('REMOTE_ADDR')
                    )
                    
                    return redirect('adminpanel:dashboard')
                else:
                    return render(request, 'adminpanel/login.html', {
                        'error': 'Admin account is inactive'
                    })
            except AdminUser.DoesNotExist:
                return render(request, 'adminpanel/login.html', {
                    'error': 'User is not registered as an admin'
                })
        else:
            return render(request, 'adminpanel/login.html', {
                'error': 'Invalid username or password'
            })
    
    return render(request, 'adminpanel/login.html')

@login_required
def admin_logout(request):
    """Admin logout"""
    # Log the action
    AuditLog.log_action(
        user=request.user,
        action='logout',
        description="Admin logged out",
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    logout(request)
    return redirect('adminpanel:login')
