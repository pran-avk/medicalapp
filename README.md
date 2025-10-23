# SmartQueue – Medical Token Management System

A powerful **Django-based queue management platform** designed to streamline patient flow in hospitals and clinics. SmartQueue offers **real-time token tracking**, **SMS/WhatsApp notifications**, and **dedicated dashboards** for patients, doctors, and administrators.

---

## 🚀 Key Features

### 🏥 Core Functionality

* **Automatic Token Generation** – Sequential tokens per department, reset daily
* **Live Queue Tracking** – Real-time WebSocket-based updates
* **Multi-Department Management** – Configure multiple hospital departments
* **Priority Queuing** – Handles normal, high, and emergency priorities
* **Smart Notifications** – Twilio integration for SMS/WhatsApp alerts

### 👨‍⚕️ Doctor Dashboard

* Monitor patient queues in real-time
* Call the next patient instantly
* Start and end consultations
* View daily consultation statistics
* Manage availability status

### 👨‍💼 Admin Panel

* Manage doctors and departments
* Track queues and analytics
* Configure system settings
* Send broadcast notifications
* Generate usage and performance reports

### 👤 Patient Portal

* Easy online registration
* Live queue position updates
* Estimated waiting time
* Feedback submission
* Real-time notification alerts

---

## 🧩 Technology Stack

| Component            | Technology                       |
| -------------------- | -------------------------------- |
| **Backend**          | Django 5.2.7                     |
| **Database**         | SQLite (Dev) / PostgreSQL (Prod) |
| **Real-time Engine** | Django Channels + WebSockets     |
| **Task Queue**       | Celery + Redis                   |
| **Notifications**    | Twilio API                       |
| **Frontend**         | Bootstrap 5 + Vanilla JS         |
| **API Layer**        | Django REST Framework            |

---

## ⚙️ Installation Guide

### Prerequisites

* Python 3.8+
* Redis Server (for WebSockets & Celery)
* Twilio Account (for SMS/WhatsApp)

### Step-by-Step Setup

#### 1️⃣ Clone & Setup Environment

```bash
git clone <repository_url>
cd smartqueue

python -m venv smartqueue_env
# Activate
smartqueue_env\Scripts\activate  # Windows
source smartqueue_env/bin/activate  # Linux/Mac

pip install django djangorestframework django-cors-headers twilio channels channels-redis celery redis
```

#### 2️⃣ Database Configuration

```bash
python manage.py makemigrations
python manage.py migrate
```

#### 3️⃣ Load Demo Data

```bash
python manage.py setup_smartqueue --demo-data
```

#### 4️⃣ Twilio Configuration (Optional)

In `smartqueue/settings.py`:

```python
TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'
```

#### 5️⃣ Start Services

```bash
# Terminal 1
redis-server

# Terminal 2
celery -A smartqueue worker --loglevel=info

# Terminal 3
python manage.py runserver
```

---

## 🌐 Access Points

| Interface                | URL                                                                                  |
| ------------------------ | ------------------------------------------------------------------------------------ |
| **Patient Registration** | [http://127.0.0.1:8000/patients/register/](http://127.0.0.1:8000/patients/register/) |
| **Doctor Login**         | [http://127.0.0.1:8000/doctors/login/](http://127.0.0.1:8000/doctors/login/)         |
| **Admin Panel**          | [http://127.0.0.1:8000/adminpanel/login/](http://127.0.0.1:8000/adminpanel/login/)   |
| **Django Admin**         | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)                         |

### Default Credentials

| Role      | Username      | Password  | Access                |
| --------- | ------------- | --------- | --------------------- |
| Superuser | admin         | admin123  | Full access           |
| Doctor    | dr.smith      | doctor123 | Sample doctor account |
| Admin     | admin.manager | admin123  | Sample admin account  |

---

## 📡 API Endpoints

### Patient APIs

* `POST /patients/api/register/` – Register new patient
* `GET /patients/api/departments/` – List departments
* `GET /patients/api/queue/{dept_id}/` – Get queue status
* `GET /patients/api/patient/{patient_id}/status/` – Get patient status
* `POST /patients/api/check-patient/` – Verify existing patient
* `POST /patients/api/feedback/` – Submit feedback

### Doctor APIs

* `GET /doctors/api/` – Fetch dashboard data
* `POST /doctors/api/` – Call next, start or complete consultation
* `POST /doctors/api/schedule/` – Update schedule

### Admin APIs

* `GET /adminpanel/api/` – Admin dashboard data
* `POST /adminpanel/api/` – Department/queue management

---

## 🔌 WebSocket Connections

| Purpose         | URL                                             |
| --------------- | ----------------------------------------------- |
| Queue Updates   | `ws://localhost:8000/ws/queue/{department_id}/` |
| Patient Updates | `ws://localhost:8000/ws/patient/{patient_id}/`  |
| Doctor Updates  | `ws://localhost:8000/ws/doctor/{doctor_id}/`    |

---

## 🧱 Database Models

### Core Models

* **Department** – Hospital departments
* **Patient** – Patient details
* **Queue** – Queue entries and tokens
* **Doctor** – Doctor information
* **PatientFeedback** – Feedback records

### Admin Models

* **AdminUser** – Admin profiles
* **DepartmentAnalytics** – Daily stats
* **SystemConfiguration** – System settings
* **AuditLog** – Activity logs

### Notification Models

* **NotificationTemplate** – Message templates
* **Notification** – Sent messages
* **NotificationPreference** – User preferences

---

## 🛠️ Deployment Guide

### Environment Variables

```bash
export DEBUG=False
export SECRET_KEY=your_secret_key
export DATABASE_URL=postgresql://user:pass@localhost/smartqueue
export REDIS_URL=redis://localhost:6379/0
export TWILIO_ACCOUNT_SID=your_sid
export TWILIO_AUTH_TOKEN=your_token
```

### Database Setup

```python
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

### Static Files

```bash
python manage.py collectstatic
```

### Production Server

```bash
pip install gunicorn daphne

gunicorn smartqueue.wsgi:application  # HTTP
daphne smartqueue.asgi:application    # WebSocket
```

---

## 🐳 Docker Setup

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "smartqueue.wsgi:application", "--bind", "0.0.0.0:8000"]
```

---

## 📈 Feature Details

### 🎫 Token Management

* Department-wise sequential numbering
* Daily auto-reset
* Priority queueing (Normal, High, Emergency)
* Real-time position tracking

### 📱 Notifications

* SMS & WhatsApp via Twilio
* Customizable message templates
* Queue status & turn alerts
* Estimated wait time updates

### 📊 Analytics

* Daily stats per department
* Doctor performance metrics
* Patient satisfaction scores
* Average wait-time reports
* Peak hour analysis

### 🔒 Security

* Role-based access control
* Authentication & CSRF protection
* Activity audit logs
* Input validation

---

## 🧰 Customization

### Add a Department

```python
Department.objects.create(
    name="Dermatology",
    description="Skin and hair care department"
)
```

### Add Custom Notification Template

```python
NotificationTemplate.objects.create(
    name="Custom Alert",
    template_type="custom",
    sms_template="Hello {name}, your appointment is scheduled for {time}."
)
```

### Modify Queue Priority Logic

Override `Queue.get_position_in_queue()` to define custom priority rules.

---

## ⚠️ Troubleshooting

| Issue                           | Possible Fix                                           |
| ------------------------------- | ------------------------------------------------------ |
| **WebSocket Connection Failed** | Ensure Redis is running, check ASGI setup              |
| **SMS Not Sending**             | Verify Twilio credentials & Celery worker              |
| **Database Errors**             | Run `python manage.py migrate` and confirm DB settings |

Set `DEBUG = True` in `settings.py` for detailed error logs during development.

---

## 🤝 Contributing

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push: `git push origin feature/your-feature`
5. Submit a pull request

---

## 📜 License

Licensed under the **MIT License**. See the LICENSE file for details.

---


## 🧭 Roadmap

| Feature                           | Status    |
| --------------------------------- | --------- |
| Mobile App (Flutter/React Native) | ⏳ Planned |
| Video Consultations               | ⏳ Planned |
| Appointment Scheduling            | ⏳ Planned |
| Multi-language Support            | ⏳ Planned |
| Advanced Analytics Dashboard      | ⏳ Planned |
| Payment Integration               | ⏳ Planned |
| Insurance Verification            | ⏳ Planned |
| Prescription Management           | ⏳ Planned |

---

**SmartQueue** – Making healthcare queues smarter, faster, and more connected. 🏥✨
