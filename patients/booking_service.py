"""
Booking Service for Online Appointments
Handles: Online booking, QR code generation, booking activation
"""

import qrcode
import io
import base64
import uuid
from django.utils import timezone
from django.db import transaction
from datetime import datetime, timedelta

from .models import Patient, Queue, Department
from doctors.models import Doctor


class BookingService:
    """Handles all booking-related operations"""
    
    def generate_booking_qr_code(self, booking_id):
        """Generate QR code for a booking"""
        # Create unique QR code data
        qr_data = f"SMARTQUEUE:BOOKING:{booking_id}:{uuid.uuid4().hex[:8]}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return qr_data, f"data:image/png;base64,{img_str}"
    
    def create_online_booking(self, patient_data, department_id, doctor_id=None, booking_date=None, time_slot=None):
        """
        Create an online booking from home
        Patient books in advance, gets QR code to scan at hospital
        """
        try:
            with transaction.atomic():
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
                
                # Get preferred doctor if specified
                preferred_doctor = None
                if doctor_id:
                    try:
                        preferred_doctor = Doctor.objects.get(id=doctor_id, department=department)
                    except Doctor.DoesNotExist:
                        pass
                
                # Set booking date (default to today if not specified)
                if not booking_date:
                    booking_date = timezone.now().date()
                
                # Check if patient already has a booking for this date
                existing_booking = Queue.objects.filter(
                    patient=patient,
                    booking_date=booking_date,
                    status__in=['booked', 'arrived', 'waiting', 'in_consultation']
                ).first()
                
                if existing_booking:
                    return {
                        'success': False,
                        'message': 'You already have a booking for this date',
                        'existing_booking_id': existing_booking.id
                    }
                
                # Create booking entry (status = 'booked', not in queue yet)
                booking = Queue.objects.create(
                    patient=patient,
                    department=department,
                    preferred_doctor=preferred_doctor,
                    status='booked',  # Booked but not arrived
                    is_online_booking=True,
                    booked_at=timezone.now(),
                    booking_date=booking_date,
                    booking_time_slot=time_slot,
                    priority=patient_data.get('priority', 'normal'),
                    notes=patient_data.get('notes', ''),
                    token_number=0  # Will be assigned when they scan QR at hospital
                )
                
                # Generate QR code
                qr_code_data, qr_code_image = self.generate_booking_qr_code(booking.id)
                booking.qr_code = qr_code_data
                booking.save()
                
                return {
                    'success': True,
                    'booking_id': booking.id,
                    'qr_code': qr_code_data,
                    'qr_code_image': qr_code_image,
                    'booking_date': booking_date.isoformat(),
                    'department': department.name,
                    'preferred_doctor': preferred_doctor.name if preferred_doctor else None,
                    'time_slot': time_slot,
                    'patient_name': patient.name,
                    'message': 'Booking successful! Please scan this QR code at hospital reception.'
                }
                
        except Department.DoesNotExist:
            return {
                'success': False,
                'message': 'Department not found or inactive'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error creating booking: {str(e)}'
            }
    
    def activate_booking_by_qr(self, qr_code_data):
        """
        Activate booking when patient scans QR at hospital reception
        Moves from 'booked' to 'arrived' and assigns token number
        """
        try:
            with transaction.atomic():
                # Find booking by QR code
                booking = Queue.objects.select_for_update().get(qr_code=qr_code_data)
                
                # Check if already activated
                if booking.status not in ['booked']:
                    return {
                        'success': False,
                        'message': f'Booking already {booking.status}',
                        'current_status': booking.status
                    }
                
                # Check if booking is for today
                today = timezone.now().date()
                if booking.booking_date and booking.booking_date != today:
                    return {
                        'success': False,
                        'message': f'This booking is for {booking.booking_date}, not today ({today})'
                    }
                
                # Assign token number NOW
                booking.token_number = booking.department.get_current_token_number()
                booking.status = 'waiting'  # Move directly to waiting queue
                booking.arrived_at = timezone.now()
                booking.save()
                
                # Calculate wait time
                booking.calculate_estimated_wait_time()
                
                return {
                    'success': True,
                    'booking_id': booking.id,
                    'token_number': booking.token_number,
                    'patient_name': booking.patient.name,
                    'department': booking.department.name,
                    'status': booking.status,
                    'position': booking.get_position_in_queue(),
                    'estimated_wait_time': booking.estimated_wait_time,
                    'message': f'Welcome! Your token number is {booking.token_number}'
                }
                
        except Queue.DoesNotExist:
            return {
                'success': False,
                'message': 'Invalid QR code or booking not found'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error activating booking: {str(e)}'
            }
    
    def get_booking_details(self, booking_id):
        """Get details of a specific booking"""
        try:
            booking = Queue.objects.get(id=booking_id)
            
            return {
                'success': True,
                'booking': {
                    'id': booking.id,
                    'token_number': booking.token_number if booking.token_number else 'Not assigned yet',
                    'patient_name': booking.patient.name,
                    'phone_number': booking.patient.phone_number,
                    'department': booking.department.name,
                    'preferred_doctor': booking.preferred_doctor.name if booking.preferred_doctor else 'Any available',
                    'status': booking.status,
                    'booking_date': booking.booking_date.isoformat() if booking.booking_date else None,
                    'time_slot': booking.booking_time_slot,
                    'booked_at': booking.booked_at.isoformat() if booking.booked_at else None,
                    'arrived_at': booking.arrived_at.isoformat() if booking.arrived_at else None,
                    'is_online_booking': booking.is_online_booking,
                    'qr_code': booking.qr_code,
                }
            }
        except Queue.DoesNotExist:
            return {
                'success': False,
                'message': 'Booking not found'
            }
    
    def cancel_booking(self, booking_id):
        """Cancel a booking"""
        try:
            booking = Queue.objects.get(id=booking_id, status__in=['booked', 'arrived'])
            booking.status = 'cancelled'
            booking.save()
            
            return {
                'success': True,
                'message': 'Booking cancelled successfully'
            }
        except Queue.DoesNotExist:
            return {
                'success': False,
                'message': 'Booking not found or cannot be cancelled'
            }
    
    def get_available_time_slots(self, department_id, date):
        """Get available time slots for a department on a specific date"""
        # Simple time slots - can be enhanced based on doctor schedules
        time_slots = [
            '09:00-10:00',
            '10:00-11:00',
            '11:00-12:00',
            '14:00-15:00',
            '15:00-16:00',
            '16:00-17:00',
        ]
        
        # Check how many bookings exist for each slot
        bookings_per_slot = {}
        for slot in time_slots:
            count = Queue.objects.filter(
                department_id=department_id,
                booking_date=date,
                booking_time_slot=slot,
                status__in=['booked', 'arrived', 'waiting']
            ).count()
            bookings_per_slot[slot] = count
        
        return {
            'success': True,
            'time_slots': [
                {
                    'slot': slot,
                    'bookings': bookings_per_slot.get(slot, 0),
                    'available': bookings_per_slot.get(slot, 0) < 10  # Max 10 per slot
                }
                for slot in time_slots
            ]
        }
