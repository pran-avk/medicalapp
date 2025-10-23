from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/queue/(?P<department_id>\w+)/$', consumers.QueueConsumer.as_asgi()),
    re_path(r'ws/patient/(?P<patient_id>\w+)/$', consumers.PatientConsumer.as_asgi()),
    re_path(r'ws/doctor/(?P<doctor_id>\w+)/$', consumers.DoctorConsumer.as_asgi()),
]