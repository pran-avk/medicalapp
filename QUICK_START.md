# ⚡ SmartQueue - Quick Start Commands

## 🚀 First Time Setup (5 Minutes)

```powershell
# 1. Go to project folder
cd E:\medicalapp

# 2. Create virtual environment
python -m venv smartqueue_env

# 3. Activate it
smartqueue_env\Scripts\Activate.ps1

# 4. Install packages
pip install -r requirements.txt

# 5. Setup database
python manage.py migrate

# 6. Create admin
python manage.py createsuperuser
# Enter: username=admin, password=admin123

# 7. Start server
python manage.py runserver
```

**✅ Done! Visit:** http://127.0.0.1:8000/

---

## 🔄 Daily Start (2 Commands)

```powershell
# 1. Activate environment
cd E:\medicalapp
smartqueue_env\Scripts\Activate.ps1

# 2. Start server
python manage.py runserver
```

**✅ Visit:** http://127.0.0.1:8000/

---

## 🌐 Important URLs

| Page | URL |
|------|-----|
| **Home** | http://127.0.0.1:8000/ |
| **Patient Register** | http://127.0.0.1:8000/patients/register/ |
| **Doctor Login** | http://127.0.0.1:8000/doctors/login/ |
| **Doctor Register** | http://127.0.0.1:8000/doctors/register/ |
| **Doctor Dashboard** | http://127.0.0.1:8000/doctors/dashboard/ |
| **Admin Panel** | http://127.0.0.1:8000/adminpanel/ |
| **Django Admin** | http://127.0.0.1:8000/admin/ |

---

## 👤 Demo Credentials

**Doctor Account:**
- Username: `dr.smith`
- Password: `doctor123`

**Admin Account:**
- Username: `admin`
- Password: `admin123`

---

## 🛑 Stop Server

Press: **Ctrl + C**

---

## 🐛 Common Fixes

**Problem:** "python not recognized"
```powershell
# Check if Python installed
python --version
```

**Problem:** "Permission denied"
```powershell
# Run as Administrator or:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Problem:** "Port 8000 in use"
```powershell
# Use different port
python manage.py runserver 8080
```

**Problem:** Missing packages
```powershell
# Reinstall
pip install -r requirements.txt
```

---

## 📦 What's in requirements.txt

- Django 5.2.7
- Django REST Framework
- Channels (WebSocket)
- QR Code Generator
- Pillow (Image Processing)
- Celery (Background Tasks)
- Twilio (SMS Notifications)
- And more...

---

## ✅ Quick Health Check

After starting server, test these:

1. ✅ Home page loads: http://127.0.0.1:8000/
2. ✅ Can register patient
3. ✅ Can login as doctor
4. ✅ Doctor dashboard works
5. ✅ Can register new doctor
6. ✅ Admin panel accessible

---

## 📁 Project Structure

```
medicalapp/
├── manage.py           ← Main command file
├── requirements.txt    ← Package list
├── db.sqlite3         ← Database
├── smartqueue/        ← Main settings
├── patients/          ← Patient app
├── doctors/           ← Doctor app
├── adminpanel/        ← Admin app
├── notifications/     ← Notifications
├── templates/         ← HTML templates
└── static/           ← CSS, JS, images
```

---

**Need detailed guide?** Read `SETUP_GUIDE.md`
