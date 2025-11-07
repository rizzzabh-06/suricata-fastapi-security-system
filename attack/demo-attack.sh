#!/bin/bash
# Complete attack demonstration script
# Usage: ./demo-attack.sh <target-url>

TARGET=${1:-"http://localhost:8000"}

echo "🎯 Starting Attack Demonstration"
echo "Target: $TARGET"
echo "================================"
echo ""

echo "Phase 1: Normal Traffic (10 sec)"
for i in {1..10}; do
    curl -s "$TARGET/api/health" > /dev/null
    sleep 1
done

echo "Phase 2: SQLi Attempts (5 attacks)"
for i in {1..5}; do
    curl -s "$TARGET/?id=1' UNION SELECT * FROM users--" > /dev/null
    echo "  → SQLi attack $i sent"
    sleep 1
done

echo "Phase 3: XSS Attempts (5 attacks)"
for i in {1..5}; do
    curl -s "$TARGET/?q=<script>alert('xss')</script>" > /dev/null
    echo "  → XSS attack $i sent"
    sleep 1
done

echo "Phase 4: Directory Traversal (5 attacks)"
for i in {1..5}; do
    curl -s "$TARGET/../../../etc/passwd" > /dev/null
    echo "  → Path traversal $i sent"
    sleep 1
done

echo "Phase 5: HIGH VOLUME FLOOD (200 req/sec for 10 sec)"
echo "  ⚠️  This will trigger PPS threshold alert!"
for sec in {1..10}; do
    for i in {1..200}; do
        curl -s "$TARGET/api/health" > /dev/null &
    done
    echo "  → Flood second $sec/10 (200 req/sec)"
    sleep 1
done

wait

echo ""
echo "✅ Attack demonstration complete!"
echo "Check dashboard at $TARGET for:"
echo "  - Alerts in Alerts tab"
echo "  - High PPS in Top Talkers"
echo "  - Red alert events in Live Events"
