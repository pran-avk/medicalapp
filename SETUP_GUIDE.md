# 🚀 SmartQueue Setup Guide - Step by Step

## Prerequisites
- Python 3.12 installed
- Git (optional, if cloning from repository)

---

## 📦 Step 1: Extract the Project
```powershell
# Navigate to where you extracted the medicalapp folder
cd E:\medicalapp
# (or wherever you placed the folder)
```

---

## 🐍 Step 2: Create Virtual Environment (Recommended)
```powershell
# Create a virtual environment
python -m venv smartqueue_env

# Activate the virtual environment
# On Windows PowerShell:
smartqueue_env\Scripts\Activate.ps1

# On Windows CMD:
smartqueue_env\Scripts\activate.bat

# On Mac/Linux:
source smartqueue_env/bin/activate
```

**Note:** You should see `(smartqueue_env)` appear in your terminal prompt.

---

## 📥 Step 3: Install Required Packages
```powershell
# Install all dependencies
pip install -r requirements.txt

# If the above fails, install packages individually:
pip install Django==5.2.7
pip install djangorestframework==3.16.1
pip install django-cors-headers==4.4.0
pip install twilio==9.2.4
pip install channels==4.3.1
pip install channels-redis==4.3.0
pip install celery==5.4.0
pip install redis==6.4.0
pip install pytz==2025.2
pip install cryptography==46.0.2
pip install qrcode==8.2
pip install Pillow==11.3.0
```

---

## 🗄️ Step 4: Set Up the Database
```powershell
# Apply database migrations
python manage.py migrate
```

Expected output:
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, patients, doctors, adminpanel, notifications
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  ...
```

---

## 👤 Step 5: Create Superuser (Admin Account)
```powershell
# Create admin account
python manage.py createsuperuser
```

Follow the prompts:
- **Username:** `admin` (or your choice)
- **Email:** `admin@smartqueue.com` (or leave blank)
- **Password:** `admin123` (or your secure password)
- **Password (again):** `admin123`

---

## 🏥 Step 6: Load Sample Data (Optional but Recommended)
```powershell
# Create sample departments and doctors
python manage.py shell
```

Then paste this in the Python shell:
```python
from patients.models import Department
from doctors.models import Doctor
from django.contrib.auth.models import User

# Create departments
departments = [
    {'name': 'General Medicine', 'description': 'General health checkups'},
    {'name': 'Cardiology', 'description': 'Heart and cardiovascular care'},
    {'name': 'Pediatrics', 'description': 'Child healthcare'},
    {'name': 'Orthopedics', 'description': 'Bone and joint care'},
    {'name': 'Dermatology', 'description': 'Skin care'},
]

for dept_data in departments:
    Department.objects.get_or_create(
        name=dept_data['name'],
        defaults={'description': dept_data['description'], 'is_active': True}
    )

print("✅ Sample departments created!")

# Create a sample doctor
dept = Department.objects.first()
user, created = User.objects.get_or_create(
    username='dr.smith',
    defaults={'email': 'smith@hospital.com', 'is_active': True}
)
if created:
    user.set_password('doctor123')
    user.save()

doctor, created = Doctor.objects.get_or_create(
    user=user,
    defaults={
        'name': 'Dr. John Smith',
        'department': dept,
        'specialization': 'General Medicine',
        'phone_number': '+1234567890'
    }
)

print("✅ Sample doctor created!")
print(f"   Username: dr.smith")
print(f"   Password: doctor123")

# Exit the shell
exit()
```

---

## 🎯 Step 7: Start the Development Server
```powershell
# Start the server
python manage.py runserver
```

Expected output:
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
October 09, 2025 - 19:30:00
Django version 5.2.7, using settings 'smartqueue.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

---

## 🌐 Step 8: Access the Application

Open your web browser and visit:

### **Main Application:**
- **Home Page:** http://127.0.0.1:8000/
- **Patient Registration:** http://127.0.0.1:8000/patients/register/
- **Doctor Login:** http://127.0.0.1:8000/doctors/login/
- **Doctor Registration:** http://127.0.0.1:8000/doctors/register/
- **Admin Panel:** http://127.0.0.1:8000/adminpanel/

### **Django Admin (for system management):**
- **Django Admin:** http://127.0.0.1:8000/admin/
  - Username: `admin`
  - Password: `admin123` (or what you set)

### **Demo Credentials:**
- **Doctor Login:**
  - Username: `dr.smith`
  - Password: `doctor123`

- **Admin Login:**
  - Username: `admin`
  - Password: `admin123`

---

## 🛑 Step 9: Stop the Server
When you want to stop the server:
```
Press: Ctrl + C
```

---

## 🔄 Step 10: Restart Later
When you come back to work on the project:

```powershell
# 1. Navigate to project folder
cd E:\medicalapp

# 2. Activate virtual environment
smartqueue_env\Scripts\Activate.ps1

# 3. Start server
python manage.py runserver
```

---

## 🐛 Troubleshooting Common Issues

### Issue 1: "python is not recognized"
**Solution:** Make sure Python is installed and added to PATH
```powershell
# Check Python installation
python --version
```

### Issue 2: "Permission denied" when activating virtual environment
**Solution:** Run PowerShell as Administrator or change execution policy
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue 3: "No module named 'django'"
**Solution:** Make sure virtual environment is activated and packages are installed
```powershell
smartqueue_env\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Issue 4: "Port 8000 already in use"
**Solution:** Use a different port
```powershell
python manage.py runserver 8080
# Then visit http://127.0.0.1:8080/
```

### Issue 5: "Redis connection error"
**Solution:** This is already fixed! The app uses in-memory channels for development.

---

## 📋 Quick Start Commands (All in One)

If you want to run everything quickly:

```powershell
# Navigate to project
cd E:\medicalapp

# Create and activate virtual environment
python -m venv smartqueue_env
smartqueue_env\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py migrate

# Create admin user
python manage.py createsuperuser

# Start server
python manage.py runserver
```

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Can access home page: http://127.0.0.1:8000/
- [ ] Can register as patient
- [ ] Can login as doctor (`dr.smith` / `doctor123`)
- [ ] Can see doctor dashboard
- [ ] Can register new doctor
- [ ] Can access admin panel
- [ ] Can see departments in database

---

## 📞 Features to Test

1. **Patient Registration:**
   - Go to http://127.0.0.1:8000/patients/register/
   - Fill form and submit
   - Get token number

2. **Doctor Dashboard:**
   - Login at http://127.0.0.1:8000/doctors/login/
   - See waiting queue
   - Call next patient
   - Mark as completed

3. **Doctor Registration:**
   - Go to http://127.0.0.1:8000/doctors/register/
   - Fill registration form
   - Wait for admin approval
   - Admin approves in Django admin

4. **Admin Panel:**
   - Login at http://127.0.0.1:8000/adminpanel/
   - View statistics
   - Manage departments
   - View audit logs

---

## 🎉 You're All Set!

The SmartQueue Medical Token Management System is now running!

**Important URLs to Bookmark:**
- Home: http://127.0.0.1:8000/
- Doctor Dashboard: http://127.0.0.1:8000/doctors/dashboard/
- Admin Panel: http://127.0.0.1:8000/adminpanel/
- Django Admin: http://127.0.0.1:8000/admin/

**Need Help?** Check the documentation files:
- `BOOKING_SYSTEM_IMPLEMENTED.md` - Booking system details
- `DOCTOR_REGISTRATION_GUIDE.md` - Doctor registration guide
- `REDIS_ERROR_FIXED.md` - Redis configuration info

---

**Happy Coding! 🚀**
