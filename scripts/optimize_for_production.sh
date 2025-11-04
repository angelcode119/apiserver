#!/bin/bash

set -e

echo "Optimizing server for production..."
echo "========================================"
echo ""

echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found. Please install Python 3.8+"
    exit 1
fi
echo "✓ Python 3: $(python3 --version)"

if ! command -v pip3 &> /dev/null; then
    echo "✗ pip3 not found. Installing..."
    sudo apt-get install python3-pip -y
fi
echo "✓ pip3 installed"

if ! command -v mongosh &> /dev/null && ! command -v mongo &> /dev/null; then
    echo "⚠️  MongoDB client not found. Skipping DB checks."
else
    echo "✓ MongoDB client found"
fi

echo ""

echo "Installing Python dependencies..."
pip3 install -r requirements.txt

pip3 install gunicorn redis aioredis

echo "✓ Dependencies installed"
echo ""

echo "Creating database indexes..."
python3 scripts/create_indexes.py

echo "✓ Database indexes created"
echo ""

echo "Checking Redis..."

if ! command -v redis-server &> /dev/null; then
    echo "Installing Redis..."
    sudo apt-get update
    sudo apt-get install redis-server -y
    
    sudo sed -i 's/^maxmemory .*/maxmemory 1gb/' /etc/redis/redis.conf
    sudo sed -i 's/^# maxmemory-policy .*/maxmemory-policy allkeys-lru/' /etc/redis/redis.conf
    
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
    
    echo "✓ Redis installed and configured"
else
    echo "✓ Redis already installed"
    
    if ! sudo systemctl is-active --quiet redis-server; then
        echo "Starting Redis..."
        sudo systemctl start redis-server
    fi
fi

if redis-cli ping &> /dev/null; then
    echo "✓ Redis is running"
else
    echo "⚠️  Redis is not responding"
fi

echo ""

echo "Checking Nginx..."

if ! command -v nginx &> /dev/null; then
    read -p "Install Nginx as reverse proxy? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing Nginx..."
        sudo apt-get install nginx -y
        echo "✓ Nginx installed"
        echo "⚠️  Please configure Nginx manually"
    fi
else
    echo "✓ Nginx already installed"
fi

echo ""

echo "Creating directories..."

mkdir -p logs
mkdir -p tmp
mkdir -p backups

echo "✓ Directories created"
echo ""

echo "Creating systemd service..."

cat > /tmp/parental-control.service << EOF
[Unit]
Description=Parental Control API
After=network.target mongodb.service redis.service
Wants=redis.service

[Service]
Type=notify
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$(which gunicorn) app.main:app \\
    --workers 4 \\
    --worker-class uvicorn.workers.UvicornWorker \\
    --bind 0.0.0.0:8000 \\
    --timeout 60 \\
    --keep-alive 5 \\
    --log-level info \\
    --access-logfile logs/access.log \\
    --error-logfile logs/error.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo mv /tmp/parental-control.service /etc/systemd/system/
sudo systemctl daemon-reload

echo "✓ Systemd service created"
echo ""

echo "========================================"
echo "✓ Optimization Complete!"
echo "========================================"
echo ""
echo "What was done:"
echo "   ✓ Dependencies installed"
echo "   ✓ Database indexes created"
echo "   ✓ Redis installed and configured"
echo "   ✓ Systemd service created"
echo ""
echo "To start the server:"
echo "   sudo systemctl start parental-control"
echo "   sudo systemctl enable parental-control"
echo ""
echo "Check status:"
echo "   sudo systemctl status parental-control"
echo ""
echo "View logs:"
echo "   tail -f logs/access.log"
echo "   tail -f logs/error.log"
echo ""
echo "Configuration:"
echo "   ✓ Workers: 4"
echo "   ✓ Port: 8000"
echo "   ✓ Redis: localhost:6379"
echo "   ✓ MongoDB: localhost:27017"
echo ""
echo "Ready for production!"
echo "========================================"
