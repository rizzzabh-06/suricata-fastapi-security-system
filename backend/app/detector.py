from collections import deque, defaultdict
import time
import heapq
import os
from typing import Optional, List, Dict
from app.utils.cmsketch import CountMinSketch
from app.utils.bloom import BloomFilter
from app.schema import AlertMsg, TopTalker

class DetectionEngine:
    """DSA-based detection engine.
    Config: WINDOW_SECS, PPS_THRESHOLD via env or defaults.
    """
    def __init__(self):
        self.window_secs = int(os.getenv("WINDOW_SECS", "60"))
        self.pps_threshold = float(os.getenv("PPS_THRESHOLD", "100"))
        
        # Sliding window: IP -> deque of timestamps
        self.windows: Dict[str, deque] = defaultdict(lambda: deque())
        
        # Count-Min Sketch for top talkers
        self.cm_sketch = CountMinSketch()
        
        # Bloom filter for IOC prefilter
        self.ioc_filter = BloomFilter()
        
        # Alert ring buffer (last N alerts)
        self.alerts: deque = deque(maxlen=1000)
        
        # Top-k heap
        self.top_k = 20
    
    def on_event(self, eve_obj: dict) -> Optional[AlertMsg]:
        """Process EVE event, return alert if threshold exceeded."""
        src_ip = eve_obj.get("src_ip")
        if not src_ip:
            return None
        
        timestamp = time.time()
        event_type = eve_obj.get("event_type", "")
        
        # Update sliding window
        window = self.windows[src_ip]
        window.append(timestamp)
        
        # Remove old timestamps outside window
        cutoff = timestamp - self.window_secs
        while window and window[0] < cutoff:
            window.popleft()
        
        # Update Count-Min Sketch
        self.cm_sketch.add(src_ip)
        
        # Calculate PPS
        pps = len(window) / self.window_secs if self.window_secs > 0 else 0
        
        # Check for alerts
        alert = None
        
        # PPS threshold alert
        if pps > self.pps_threshold:
            alert = AlertMsg(
                timestamp=eve_obj.get("timestamp", ""),
                severity="high",
                src_ip=src_ip,
                dest_ip=eve_obj.get("dest_ip"),
                reason=f"High PPS detected: {pps:.1f} pps (threshold: {self.pps_threshold})",
                raw=eve_obj
            )
        
        # Suricata alert event
        elif event_type == "alert":
            alert_data = eve_obj.get("alert", {})
            alert = AlertMsg(
                timestamp=eve_obj.get("timestamp", ""),
                severity=alert_data.get("severity", "medium").lower(),
                src_ip=src_ip,
                dest_ip=eve_obj.get("dest_ip"),
                reason=alert_data.get("signature", "Suricata alert"),
                raw=eve_obj
            )
        
        if alert:
            self.alerts.append(alert)
        
        return alert
    
    def get_top_talkers(self, limit: int = 20) -> List[TopTalker]:
        """Get top-k IPs by packet count using heap."""
        ip_counts = []
        for ip, window in self.windows.items():
            count = len(window)
            if count > 0:
                heapq.heappush(ip_counts, (-count, ip, count))
        
        top = heapq.nsmallest(limit, ip_counts)
        return [
            TopTalker(
                ip=ip,
                pps=count / self.window_secs if self.window_secs > 0 else 0,
                total_packets=count
            )
            for _, ip, count in top
        ]
    
    def get_alerts(self, limit: int = 100) -> List[AlertMsg]:
        """Get recent alerts from ring buffer."""
        return list(self.alerts)[-limit:]
