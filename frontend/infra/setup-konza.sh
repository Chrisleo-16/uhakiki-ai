#!/bin/bash
# UhakikiAI Infrastructure Hardening for Konza Tier III

echo "[+] Initializing Sovereign Infrastructure..."

# 1. Create the isolated network
# --internal means containers on this network cannot talk to the outside world directly
docker network create --internal sovereign_bridge

# 2. Create Persistent Storage (Volumes)
# This ensures student data survives even if the server restarts
docker volume create milvus_data
docker volume create redis_state

# 3. Setting local Firewall Rules (Simplified)
# Only allow Port 8000 (Your API) to be visible to the public
echo "[+] Configuring Port Hardening..."
# (In production, you'd use ufw or iptables here)

echo "[+] Sovereign Bridge Established. Ready for 'docker-compose up'."