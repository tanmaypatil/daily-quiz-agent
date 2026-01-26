#!/bin/bash
# Initial setup script for Lightsail deployment
# Run this once on a fresh instance

set -e

echo "=== CLAT Quiz App - Initial Setup ==="

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nginx

# Create directories
echo "Creating directories..."
sudo mkdir -p /var/www/quiz
sudo mkdir -p /var/db
sudo chown -R ubuntu:ubuntu /var/www/quiz
sudo chown -R ubuntu:ubuntu /var/db

# Clone repository (if not already cloned)
if [ ! -d "/var/www/quiz/.git" ]; then
    echo "Cloning repository..."
    cd /var/www
    git clone https://github.com/tanmaypatil/daily-quiz-agent.git quiz
else
    echo "Repository already exists, pulling latest..."
    cd /var/www/quiz
    git pull origin main
fi

cd /var/www/quiz

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "!!! IMPORTANT: Edit /var/www/quiz/.env with your actual credentials !!!"
    echo ""
fi

# Setup systemd service
echo "Setting up systemd service..."
sudo cp deploy/quiz.service /etc/systemd/system/quiz.service
sudo systemctl daemon-reload
sudo systemctl enable quiz

# Initialize database
echo "Initializing database..."
python -c "from app import create_app; app = create_app(); ctx = app.app_context(); ctx.push(); from app.extensions import db; db.create_all()"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit /var/www/quiz/.env with your credentials"
echo "2. Configure nginx (see deploy/nginx.conf)"
echo "3. Start the service: sudo systemctl start quiz"
echo "4. Setup cron job: crontab -e"
echo "   Add: 0 2 * * * cd /var/www/quiz && venv/bin/python scripts/generate_quiz.py"
echo ""
