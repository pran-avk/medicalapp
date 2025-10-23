@echo off
echo 🏥 SmartQueue Deployment Script
echo ================================

REM Check if virtual environment exists
if not exist smartqueue_env (
    echo Creating virtual environment...
    python -m venv smartqueue_env
)

REM Activate virtual environment
echo Activating virtual environment...
call smartqueue_env\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run database migrations
echo Running database migrations...
python manage.py makemigrations
python manage.py migrate

REM Setup initial data
echo Setting up initial data...
python manage.py setup_smartqueue --demo-data

REM Collect static files
echo Collecting static files...
python manage.py collectstatic --noinput

echo.
echo ✅ Deployment completed successfully!
echo.
echo Next steps:
echo 1. Configure Twilio credentials in smartqueue/settings.py
echo 2. Start Redis server: redis-server
echo 3. Start Celery worker: celery -A smartqueue worker --loglevel=info
echo 4. Start Django server: python manage.py runserver
echo.
echo Access URLs:
echo - Patient Registration: http://127.0.0.1:8000/patients/register/
echo - Doctor Login: http://127.0.0.1:8000/doctors/login/
echo - Admin Panel: http://127.0.0.1:8000/adminpanel/login/
echo.
echo Default credentials:
echo - Superuser: admin/admin123
echo - Doctor: dr.smith/doctor123
echo - Admin: admin.manager/admin123

pause