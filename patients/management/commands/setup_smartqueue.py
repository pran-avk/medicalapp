from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from patients.models import Department, Patient, Queue
from doctors.models import Doctor
from adminpanel.models import AdminUser
from notifications.services import setup_notification_system
import random

class Command(BaseCommand):
    help = 'Set up initial demo data for SmartQueue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--demo-data',
            action='store_true',
            help='Create demo patients and queues',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up SmartQueue initial data...'))
        
        # Create superuser if it doesn't exist
        self.create_superuser()
        
        # Create departments
        self.create_departments()
        
        # Create doctors
        self.create_doctors()
        
        # Create admin users
        self.create_admin_users()
        
        # Set up notification system
        self.setup_notifications()
        
        # Create demo data if requested
        if options['demo_data']:
            self.create_demo_data()
        
        self.stdout.write(self.style.SUCCESS('Initial data setup complete!'))
        self.print_summary()

    def create_superuser(self):
        """Create a superuser if it doesn't exist"""
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@smartqueue.com',
                password='admin123',
                first_name='System',
                last_name='Administrator'
            )
            self.stdout.write(self.style.SUCCESS('Created superuser: admin/admin123'))
        else:
            self.stdout.write('Superuser already exists')

    def create_departments(self):
        """Create initial departments"""
        departments_data = [
            {
                'name': 'General Medicine',
                'description': 'General medical consultations and checkups'
            },
            {
                'name': 'Cardiology',
                'description': 'Heart and cardiovascular system specialist care'
            },
            {
                'name': 'Orthopedics',
                'description': 'Bone, joint, and muscle care'
            },
            {
                'name': 'Pediatrics',
                'description': 'Medical care for children and infants'
            },
            {
                'name': 'Dermatology',
                'description': 'Skin, hair, and nail treatments'
            },
            {
                'name': 'Emergency',
                'description': 'Emergency medical care and urgent treatment'
            }
        ]
        
        created_count = 0
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                name=dept_data['name'],
                defaults={'description': dept_data['description']}
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'Created {created_count} new departments')

    def create_doctors(self):
        """Create sample doctors"""
        doctors_data = [
            {
                'username': 'dr.smith',
                'email': 'dr.smith@hospital.com',
                'first_name': 'John',
                'last_name': 'Smith',
                'name': 'Dr. John Smith',
                'employee_id': 'DOC001',
                'phone_number': '+1234567890',
                'specialization': 'General Medicine',
                'license_number': 'LIC001',
                'years_of_experience': 10,
                'qualification': 'MBBS, MD General Medicine',
                'department': 'General Medicine'
            },
            {
                'username': 'dr.johnson',
                'email': 'dr.johnson@hospital.com',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'name': 'Dr. Sarah Johnson',
                'employee_id': 'DOC002',
                'phone_number': '+1234567891',
                'specialization': 'Cardiology',
                'license_number': 'LIC002',
                'years_of_experience': 15,
                'qualification': 'MBBS, MD Cardiology',
                'department': 'Cardiology'
            },
            {
                'username': 'dr.brown',
                'email': 'dr.brown@hospital.com',
                'first_name': 'Michael',
                'last_name': 'Brown',
                'name': 'Dr. Michael Brown',
                'employee_id': 'DOC003',
                'phone_number': '+1234567892',
                'specialization': 'Orthopedics',
                'license_number': 'LIC003',
                'years_of_experience': 12,
                'qualification': 'MBBS, MS Orthopedics',
                'department': 'Orthopedics'
            }
        ]
        
        created_count = 0
        for doctor_data in doctors_data:
            # Create user if it doesn't exist
            user, user_created = User.objects.get_or_create(
                username=doctor_data['username'],
                defaults={
                    'email': doctor_data['email'],
                    'first_name': doctor_data['first_name'],
                    'last_name': doctor_data['last_name'],
                    'is_staff': True
                }
            )
            
            if user_created:
                user.set_password('doctor123')
                user.save()
            
            # Create doctor profile
            try:
                department = Department.objects.get(name=doctor_data['department'])
                doctor, created = Doctor.objects.get_or_create(
                    user=user,
                    defaults={
                        'name': doctor_data['name'],
                        'employee_id': doctor_data['employee_id'],
                        'phone_number': doctor_data['phone_number'],
                        'email': doctor_data['email'],
                        'specialization': doctor_data['specialization'],
                        'license_number': doctor_data['license_number'],
                        'years_of_experience': doctor_data['years_of_experience'],
                        'qualification': doctor_data['qualification'],
                        'department': department
                    }
                )
                if created:
                    created_count += 1
            except Department.DoesNotExist:
                self.stdout.write(f'Department {doctor_data["department"]} not found for doctor {doctor_data["name"]}')
        
        self.stdout.write(f'Created {created_count} new doctors')

    def create_admin_users(self):
        """Create admin users"""
        admin_data = [
            {
                'username': 'admin.manager',
                'email': 'manager@hospital.com',
                'first_name': 'Jane',
                'last_name': 'Manager',
                'role': 'admin',
                'phone_number': '+1234567893'
            },
            {
                'username': 'staff.reception',
                'email': 'reception@hospital.com',
                'first_name': 'Bob',
                'last_name': 'Reception',
                'role': 'staff',
                'phone_number': '+1234567894'
            }
        ]
        
        created_count = 0
        for admin_info in admin_data:
            # Create user if it doesn't exist
            user, user_created = User.objects.get_or_create(
                username=admin_info['username'],
                defaults={
                    'email': admin_info['email'],
                    'first_name': admin_info['first_name'],
                    'last_name': admin_info['last_name'],
                    'is_staff': True
                }
            )
            
            if user_created:
                user.set_password('admin123')
                user.save()
            
            # Create admin profile
            admin_user, created = AdminUser.objects.get_or_create(
                user=user,
                defaults={
                    'role': admin_info['role'],
                    'phone_number': admin_info['phone_number']
                }
            )
            
            if created:
                # Add all departments for admin users
                if admin_info['role'] in ['admin', 'super_admin']:
                    admin_user.departments.set(Department.objects.all())
                created_count += 1
        
        self.stdout.write(f'Created {created_count} new admin users')

    def setup_notifications(self):
        """Set up notification templates"""
        setup_notification_system()
        self.stdout.write('Notification system configured')

    def create_demo_data(self):
        """Create demo patients and queue entries"""
        self.stdout.write('Creating demo data...')
        
        # Demo patients
        demo_patients = [
            {'name': 'Alice Johnson', 'phone': '+1234501001', 'email': 'alice@email.com', 'age': 35, 'gender': 'F'},
            {'name': 'Bob Smith', 'phone': '+1234501002', 'email': 'bob@email.com', 'age': 42, 'gender': 'M'},
            {'name': 'Carol Williams', 'phone': '+1234501003', 'email': 'carol@email.com', 'age': 28, 'gender': 'F'},
            {'name': 'David Brown', 'phone': '+1234501004', 'email': 'david@email.com', 'age': 55, 'gender': 'M'},
            {'name': 'Eva Davis', 'phone': '+1234501005', 'email': 'eva@email.com', 'age': 33, 'gender': 'F'},
            {'name': 'Frank Miller', 'phone': '+1234501006', 'email': 'frank@email.com', 'age': 47, 'gender': 'M'},
            {'name': 'Grace Wilson', 'phone': '+1234501007', 'email': 'grace@email.com', 'age': 29, 'gender': 'F'},
            {'name': 'Henry Taylor', 'phone': '+1234501008', 'email': 'henry@email.com', 'age': 38, 'gender': 'M'},
        ]
        
        created_patients = 0
        created_queues = 0
        
        departments = list(Department.objects.filter(is_active=True))
        
        for patient_data in demo_patients:
            # Create patient
            patient, created = Patient.objects.get_or_create(
                phone_number=patient_data['phone'],
                defaults={
                    'name': patient_data['name'],
                    'email': patient_data['email'],
                    'age': patient_data['age'],
                    'gender': patient_data['gender'],
                    'address': f"{random.randint(100, 999)} Demo Street, Demo City",
                }
            )
            
            if created:
                created_patients += 1
                
                # Create queue entry for some patients
                if random.random() < 0.7:  # 70% chance of having a queue entry
                    department = random.choice(departments)
                    priority = random.choice(['normal', 'normal', 'normal', 'high', 'emergency'])
                    status = random.choice(['waiting', 'waiting', 'waiting', 'called', 'in_consultation'])
                    
                    queue_entry = Queue.objects.create(
                        patient=patient,
                        department=department,
                        priority=priority,
                        status=status,
                        notes=f"Demo queue entry for {patient.name}"
                    )
                    
                    # Calculate estimated wait time
                    queue_entry.calculate_estimated_wait_time()
                    created_queues += 1
        
        self.stdout.write(f'Created {created_patients} demo patients and {created_queues} queue entries')

    def print_summary(self):
        """Print setup summary"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('SMARTQUEUE SETUP COMPLETE'))
        self.stdout.write('='*50)
        self.stdout.write('\nDefault Login Credentials:')
        self.stdout.write('-' * 30)
        self.stdout.write('Superuser:')
        self.stdout.write('  Username: admin')
        self.stdout.write('  Password: admin123')
        self.stdout.write('  URL: /admin/')
        self.stdout.write('')
        self.stdout.write('Sample Doctor:')
        self.stdout.write('  Username: dr.smith')
        self.stdout.write('  Password: doctor123')
        self.stdout.write('  URL: /doctors/login/')
        self.stdout.write('')
        self.stdout.write('Sample Admin:')
        self.stdout.write('  Username: admin.manager')
        self.stdout.write('  Password: admin123')
        self.stdout.write('  URL: /adminpanel/login/')
        self.stdout.write('')
        self.stdout.write('Patient Registration:')
        self.stdout.write('  URL: /patients/register/')
        self.stdout.write('')
        self.stdout.write('Queue Display:')
        self.stdout.write('  URL: /patients/queue/<department_id>/')
        self.stdout.write('')
        self.stdout.write(f'Departments: {Department.objects.count()}')
        self.stdout.write(f'Doctors: {Doctor.objects.count()}')
        self.stdout.write(f'Patients: {Patient.objects.count()}')
        self.stdout.write(f'Queue Entries: {Queue.objects.count()}')
        self.stdout.write('')
        self.stdout.write('Next Steps:')
        self.stdout.write('1. Configure Twilio credentials in settings.py')
        self.stdout.write('2. Start Redis server for WebSocket support')
        self.stdout.write('3. Start Celery worker for notifications')
        self.stdout.write('4. Run: python manage.py runserver')
        self.stdout.write('='*50)