# SmartQueue - Medical Token Management System

A comprehensive Django-based medical queue management system that provides real-time token tracking, SMS/WhatsApp notifications, and multi-role dashboards for patients, doctors, and administrators.

## Features

### 🏥 Core Functionality
- **Automatic Token Assignment**: Sequential token numbers per department per day
- **Real-time Queue Updates**: WebSocket-based live updates
- **Multi-department Support**: Manage multiple hospital departments
- **Priority Queue Management**: Support for normal, high, and emergency priorities
- **SMS/WhatsApp Notifications**: Twilio integration for patient alerts

### 👨‍⚕️ Doctor Dashboard
- View waiting patients in real-time
- Call next patient in queue
- Start and complete consultations
- Track daily patient statistics
- Manage availability status

### 👨‍💼 Admin Panel
- Department management
- Doctor management
- Live queue monitoring
- Analytics and reports
- Notification management
- System configuration

### 👤 Patient Interface
- Online registration
- Real-time status tracking
- Queue position updates
- Estimated wait times
- Feedback system

## Technology Stack

- **Backend**: Django 5.2.7
- **Database**: SQLite (development) / PostgreSQL (production)
- **Real-time**: Django Channels + WebSockets
- **Task Queue**: Celery + Redis
- **Notifications**: Twilio API
- **Frontend**: Bootstrap 5 + JavaScript
- **API**: Django REST Framework

## Installation & Setup

### Prerequisites
- Python 3.8+
- Redis Server (for WebSocket and Celery)
- Twilio Account (for SMS/WhatsApp)

### Quick Start

1. **Clone and Setup Environment**
```bash
# Clone the repository
git clone <repository_url>
cd smartqueue

# Create virtual environment
python -m venv smartqueue_env

# Activate virtual environment
# Windows:
smartqueue_env\Scripts\activate
# Linux/Mac:
source smartqueue_env/bin/activate

# Install dependencies
pip install django djangorestframework django-cors-headers twilio channels channels-redis celery redis
```

2. **Configure Database**
```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate
```

3. **Setup Initial Data**
```bash
# Create initial data with demo patients
python manage.py setup_smartqueue --demo-data
```

4. **Configure Twilio (Optional)**
Edit `smartqueue/settings.py`:
```python
TWILIO_ACCOUNT_SID = 'your_account_sid_here'
TWILIO_AUTH_TOKEN = 'your_auth_token_here'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number_here'
```

5. **Start Services**

In separate terminals:

```bash
# Terminal 1: Start Redis Server
redis-server

# Terminal 2: Start Celery Worker
celery -A smartqueue worker --loglevel=info

# Terminal 3: Start Django Server
python manage.py runserver
```

### Access URLs

- **Patient Registration**: http://127.0.0.1:8000/patients/register/
- **Doctor Login**: http://127.0.0.1:8000/doctors/login/
- **Admin Panel**: http://127.0.0.1:8000/adminpanel/login/
- **Django Admin**: http://127.0.0.1:8000/admin/

### Default Credentials

| Role | Username | Password | Description |
|------|----------|----------|-------------|
| Superuser | admin | admin123 | Full system access |
| Doctor | dr.smith | doctor123 | Sample doctor account |
| Admin | admin.manager | admin123 | Sample admin account |

## API Endpoints

### Patient APIs
- `POST /patients/api/register/` - Register new patient
- `GET /patients/api/departments/` - List departments
- `GET /patients/api/queue/{dept_id}/` - Queue status
- `GET /patients/api/patient/{patient_id}/status/` - Patient status
- `POST /patients/api/check-patient/` - Check existing patient
- `POST /patients/api/feedback/` - Submit feedback

### Doctor APIs
- `POST /doctors/api/` - Doctor operations (call next, start/complete consultation)
- `GET /doctors/api/` - Get doctor dashboard data
- `POST /doctors/api/schedule/` - Update doctor schedule

### Admin APIs
- `POST /adminpanel/api/` - Admin operations (manage departments, queues)
- `GET /adminpanel/api/` - Get admin dashboard data

## WebSocket Connections

### Real-time Updates
- **Queue Updates**: `ws://localhost:8000/ws/queue/{department_id}/`
- **Patient Updates**: `ws://localhost:8000/ws/patient/{patient_id}/`
- **Doctor Updates**: `ws://localhost:8000/ws/doctor/{doctor_id}/`

## Database Models

### Core Models
- **Department**: Hospital departments
- **Patient**: Patient information
- **Queue**: Token and queue entries
- **Doctor**: Doctor profiles
- **PatientFeedback**: Post-consultation feedback

### Admin Models
- **AdminUser**: Admin user profiles
- **DepartmentAnalytics**: Daily analytics
- **SystemConfiguration**: System settings
- **AuditLog**: Activity logging

### Notification Models
- **NotificationTemplate**: Message templates
- **Notification**: Sent notifications
- **NotificationPreference**: Patient preferences

## Deployment

### Production Setup

1. **Environment Variables**
```bash
export DEBUG=False
export SECRET_KEY=your_secret_key
export DATABASE_URL=postgresql://user:pass@localhost/smartqueue
export REDIS_URL=redis://localhost:6379/0
export TWILIO_ACCOUNT_SID=your_sid
export TWILIO_AUTH_TOKEN=your_token
```

2. **Database Configuration**
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'smartqueue',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

3. **Static Files**
```bash
python manage.py collectstatic
```

4. **Production Server**
```bash
# Using Gunicorn + Daphne
pip install gunicorn daphne

# HTTP Server
gunicorn smartqueue.wsgi:application

# WebSocket Server
daphne smartqueue.asgi:application
```

### Docker Setup

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "smartqueue.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Features in Detail

### 🎫 Token Management
- Automatic sequential numbering per department
- Daily reset of token counters
- Priority-based queue ordering
- Real-time position tracking

### 📱 Notifications
- SMS alerts via Twilio
- WhatsApp message support
- Customizable message templates
- Queue status notifications
- Turn approaching alerts

### 📊 Analytics
- Daily department statistics
- Doctor performance metrics
- Patient satisfaction tracking
- Wait time analysis
- Peak hour identification

### 🔒 Security
- Role-based access control
- User authentication
- Activity audit logging
- CSRF protection
- Input validation

## Customization

### Adding New Departments
```python
# Via Django Admin or API
Department.objects.create(
    name="New Department",
    description="Department description"
)
```

### Custom Notification Templates
```python
NotificationTemplate.objects.create(
    name="Custom Alert",
    template_type="custom",
    sms_template="Hello {name}, custom message here..."
)
```

### Queue Priority Rules
Modify `Queue.get_position_in_queue()` method to implement custom priority logic.

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Ensure Redis server is running
   - Check firewall settings
   - Verify ASGI configuration

2. **SMS Not Sending**
   - Verify Twilio credentials
   - Check phone number format
   - Ensure Celery worker is running

3. **Database Errors**
   - Run migrations: `python manage.py migrate`
   - Check database connection settings

### Debug Mode
Set `DEBUG = True` in settings.py for development debugging.

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Email: support@smartqueue.com
- Documentation: [Project Wiki]
- Issues: [GitHub Issues]

## Roadmap

### Upcoming Features
- [ ] Mobile app (React Native/Flutter)
- [ ] Video consultation integration
- [ ] Appointment scheduling
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Payment integration
- [ ] Insurance verification
- [ ] Prescription management

---

**SmartQueue** - Making healthcare queues smarter, one token at a time! 🏥✨#   m e d i c a l a p p  
 