#!/bin/bash

# Setup script for ThermoEngine auto-start services

echo "=== ThermoEngine Auto-Start Setup ==="
echo

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then 
   echo "Please run this script with sudo:"
   echo "sudo ./setup-autostart.sh"
   exit 1
fi

# Set correct permissions on environment file
echo "1. Setting permissions on environment file..."
chmod 600 /home/danny/thermoengine-web/thermoengine.env
chown danny:danny /home/danny/thermoengine-web/thermoengine.env

# Copy service files to systemd directory
echo "2. Installing systemd service files..."
cp /home/danny/thermoengine-web/thermoengine-openai.service /etc/systemd/system/
cp /home/danny/thermoengine-web/cloudflared-tunnel.service /etc/systemd/system/

# Reload systemd
echo "3. Reloading systemd daemon..."
systemctl daemon-reload

# Enable services
echo "4. Enabling services to start on boot..."
systemctl enable thermoengine-openai.service
systemctl enable cloudflared-tunnel.service

echo
echo "=== Setup Complete! ==="
echo
echo "IMPORTANT: Before starting the services, you need to:"
echo "1. Edit /home/danny/thermoengine-web/thermoengine.env"
echo "2. Replace 'your-actual-openai-api-key-here' with your real OpenAI API key"
echo
echo "To start the services now:"
echo "  sudo systemctl start thermoengine-openai"
echo "  sudo systemctl start cloudflared-tunnel"
echo
echo "To check service status:"
echo "  sudo systemctl status thermoengine-openai"
echo "  sudo systemctl status cloudflared-tunnel"
echo
echo "To view logs:"
echo "  tail -f /home/danny/thermoengine-web/thermoengine-service.log"
echo "  tail -f /home/danny/thermoengine-web/cloudflared-service.log"
echo
echo "To stop services:"
echo "  sudo systemctl stop thermoengine-openai"
echo "  sudo systemctl stop cloudflared-tunnel"