from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from patients.models import Department

@csrf_exempt
def test_departments(request):
    """Test endpoint to check departments"""
    departments = Department.objects.filter(is_active=True)
    dept_list = [{
        'id': d.id,
        'name': d.name,
        'is_active': d.is_active
    } for d in departments]
    
    return JsonResponse({
        'success': True,
        'count': departments.count(),
        'departments': dept_list
    })

urlpatterns = [
    path('test-departments/', test_departments, name='test_departments'),
]
