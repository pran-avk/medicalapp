#!/bin/bash

# SmartQueue Deployment Script
echo "🏥 SmartQueue Deployment Script"
echo "================================"

# Check if virtual environment exists
if [ ! -d "smartqueue_env" ]; then
    echo "Creating virtual environment..."
    python -m venv smartqueue_env
fi

# Activate virtual environment
echo "Activating virtual environment..."
source smartqueue_env/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Setup initial data
echo "Setting up initial data..."
python manage.py setup_smartqueue --demo-data

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "Next steps:"
echo "1. Configure Twilio credentials in smartqueue/settings.py"
echo "2. Start Redis server: redis-server"
echo "3. Start Celery worker: celery -A smartqueue worker --loglevel=info"
echo "4. Start Django server: python manage.py runserver"
echo ""
echo "Access URLs:"
echo "- Patient Registration: http://127.0.0.1:8000/patients/register/"
echo "- Doctor Login: http://127.0.0.1:8000/doctors/login/"
echo "- Admin Panel: http://127.0.0.1:8000/adminpanel/login/"
echo ""
echo "Default credentials:"
echo "- Superuser: admin/admin123"
echo "- Doctor: dr.smith/doctor123"  
echo "- Admin: admin.manager/admin123"