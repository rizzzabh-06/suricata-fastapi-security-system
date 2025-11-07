# Test Data for Local Development

## Quick Test (Without Suricata)

### 1. Point backend to test EVE file

```bash
cd backend
export EVE_PATH="../test-data/test-eve.json"
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Simulate traffic

In another terminal:
```bash
cd test-data
./simulate-traffic.sh test-eve.json
```

### 3. Open dashboard

Navigate to `http://localhost:8000/` and watch:
- Live events streaming
- Alerts appearing
- Top talkers populating
- KPIs updating

### 4. Test mitigation (requires sudo setup)

```bash
# Install helper script first
sudo cp ../scripts/secapp-mitigate /usr/local/bin/
sudo chown root:root /usr/local/bin/secapp-mitigate
sudo chmod 750 /usr/local/bin/secapp-mitigate

# Add sudoers entry
echo "$USER ALL=(root) NOPASSWD: /usr/local/bin/secapp-mitigate" | sudo tee /etc/sudoers.d/secapp-test
sudo chmod 440 /etc/sudoers.d/secapp-test
```

Then in dashboard:
1. Go to Mitigation tab
2. Login with `admin/admin`
3. Block an IP (e.g., `192.168.1.100`)
4. Check: `sudo iptables -L INPUT -n | grep 192.168.1.100`

## Generate High PPS Traffic

To trigger PPS threshold alerts:

```bash
# Generate 200 events/sec from same IP
while true; do
    for i in {1..200}; do
        echo "{\"timestamp\":\"$(date -u +"%Y-%m-%dT%H:%M:%S.%6N+0000")\",\"event_type\":\"flow\",\"src_ip\":\"192.168.1.50\",\"dest_ip\":\"8.8.8.8\",\"proto\":\"TCP\"}" >> test-eve.json
    done
    sleep 1
done
```

This will trigger a PPS alert (threshold: 100 pps).

## Clean Up

```bash
# Stop simulation (Ctrl+C)
# Clear test data
> test-eve.json

# Remove iptables rules
sudo iptables -F INPUT

# Remove sudoers
sudo rm /etc/sudoers.d/secapp-test
```
