#!/bin/bash
export PORT=${PORT:-5000}
export IDFACE_IP=${IDFACE_IP:-192.168.0.129}
export IDFACE_USER=${IDFACE_USER:-admin}
export IDFACE_PASSWORD=${IDFACE_PASSWORD:-123456}
export IDFACE_PORT=${IDFACE_PORT:-80}
export SECRET_KEY=${SECRET_KEY:-idface-presenca-secret-key-2024}
python app.py
