import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from patients.models import Queue, Department, Patient
from doctors.models import Doctor

class QueueConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.department_id = self.scope['url_route']['kwargs']['department_id']
        self.department_group_name = f'queue_{self.department_id}'

        # Join department group
        await self.channel_layer.group_add(
            self.department_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave department group
        await self.channel_layer.group_discard(
            self.department_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']

        if message_type == 'get_queue_status':
            queue_data = await self.get_queue_status()
            await self.send(text_data=json.dumps({
                'type': 'queue_status',
                'data': queue_data
            }))

    async def queue_update(self, event):
        # Send queue update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'queue_update',
            'data': event['data']
        }))

    @database_sync_to_async
    def get_queue_status(self):
        try:
            department = Department.objects.get(id=self.department_id)
            waiting_queue = Queue.objects.filter(
                department=department,
                status='waiting',
                created_at__date=timezone.now().date()
            ).order_by('created_at')
            
            queue_data = []
            for queue_entry in waiting_queue:
                queue_data.append({
                    'token_number': queue_entry.token_number,
                    'patient_name': queue_entry.patient.name,
                    'estimated_wait_time': queue_entry.estimated_wait_time,
                    'position': queue_entry.get_position_in_queue(),
                })
            
            return {
                'department': department.name,
                'total_waiting': len(queue_data),
                'queue': queue_data
            }
        except Department.DoesNotExist:
            return {'error': 'Department not found'}

class PatientConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.patient_id = self.scope['url_route']['kwargs']['patient_id']
        self.patient_group_name = f'patient_{self.patient_id}'

        # Join patient group
        await self.channel_layer.group_add(
            self.patient_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave patient group
        await self.channel_layer.group_discard(
            self.patient_group_name,
            self.channel_name
        )

    async def patient_update(self, event):
        # Send patient update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'patient_update',
            'data': event['data']
        }))

class DoctorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.doctor_id = self.scope['url_route']['kwargs']['doctor_id']
        self.doctor_group_name = f'doctor_{self.doctor_id}'

        # Join doctor group
        await self.channel_layer.group_add(
            self.doctor_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave doctor group
        await self.channel_layer.group_discard(
            self.doctor_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json['type']

        if message_type == 'call_next_patient':
            result = await self.call_next_patient()
            await self.send(text_data=json.dumps({
                'type': 'patient_called',
                'data': result
            }))

    async def doctor_update(self, event):
        # Send doctor update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'doctor_update',
            'data': event['data']
        }))

    @database_sync_to_async
    def call_next_patient(self):
        try:
            doctor = Doctor.objects.get(id=self.doctor_id)
            next_patient = doctor.call_next_patient()
            if next_patient:
                return {
                    'success': True,
                    'patient': {
                        'token_number': next_patient.token_number,
                        'name': next_patient.patient.name,
                        'phone': next_patient.patient.phone_number
                    }
                }
            else:
                return {'success': False, 'message': 'No patients in queue'}
        except Doctor.DoesNotExist:
            return {'success': False, 'message': 'Doctor not found'}