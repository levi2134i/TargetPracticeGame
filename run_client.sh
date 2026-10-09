#!/bin/bash
read -p "Enter Server IP (default: localhost): " IP
IP=${IP:-localhost}
echo "Connecting to $IP..."
python3 client.py $IP
