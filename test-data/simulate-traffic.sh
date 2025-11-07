#!/bin/bash
# Simulate Suricata EVE JSON events for testing
# Usage: ./simulate-traffic.sh <eve-json-path>

EVE_PATH=${1:-"./test-data/test-eve.json"}

echo "Simulating traffic to $EVE_PATH"
echo "Press Ctrl+C to stop"

while true; do
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.%6N+0000")
    SRC_IP="192.168.1.$((RANDOM % 255))"
    
    # Random event type
    if [ $((RANDOM % 10)) -eq 0 ]; then
        # Alert event (10% chance)
        echo "{\"timestamp\":\"$TIMESTAMP\",\"event_type\":\"alert\",\"src_ip\":\"$SRC_IP\",\"dest_ip\":\"10.0.0.1\",\"alert\":{\"signature\":\"Suspicious activity detected\",\"severity\":\"high\"}}" >> "$EVE_PATH"
    else
        # Normal flow event
        echo "{\"timestamp\":\"$TIMESTAMP\",\"event_type\":\"flow\",\"src_ip\":\"$SRC_IP\",\"dest_ip\":\"8.8.8.8\",\"proto\":\"TCP\"}" >> "$EVE_PATH"
    fi
    
    sleep 0.1
done
