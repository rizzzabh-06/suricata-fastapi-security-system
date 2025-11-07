import asyncio
import subprocess
import os
from datetime import datetime
from typing import Dict, List
from collections import deque
from app.schema import AuditItem

class Mitigator:
    """IP blocking/unblocking with TTL and audit log.
    Config: AUTO_MITIGATE env var (default 0).
    """
    def __init__(self):
        self.auto_mitigate = os.getenv("AUTO_MITIGATE", "0") == "1"
        self.blocked_ips: Dict[str, float] = {}  # ip -> unblock_timestamp
        self.audit_log: deque = deque(maxlen=1000)
        self.helper_path = "/usr/local/bin/secapp-mitigate"
    
    async def block_ip(self, ip: str, ttl: int, reason: str, actor: str = "system"):
        """Block IP for TTL seconds."""
        if not self.auto_mitigate and actor == "system":
            return
        
        try:
            subprocess.run(["sudo", self.helper_path, "block", ip], check=True, capture_output=True)
            unblock_ts = asyncio.get_event_loop().time() + ttl
            self.blocked_ips[ip] = unblock_ts
            
            # Schedule unblock
            asyncio.create_task(self._schedule_unblock(ip, ttl))
            
            # Audit
            self.audit_log.append(AuditItem(
                timestamp=datetime.utcnow().isoformat(),
                action="block",
                ip=ip,
                reason=reason,
                ttl=ttl,
                actor=actor
            ))
        except Exception:
            pass
    
    async def unblock_ip(self, ip: str, actor: str = "manual"):
        """Unblock IP immediately."""
        try:
            subprocess.run(["sudo", self.helper_path, "unblock", ip], check=True, capture_output=True)
            self.blocked_ips.pop(ip, None)
            
            # Audit
            self.audit_log.append(AuditItem(
                timestamp=datetime.utcnow().isoformat(),
                action="unblock",
                ip=ip,
                reason="Manual unblock",
                actor=actor
            ))
        except Exception:
            pass
    
    async def _schedule_unblock(self, ip: str, ttl: int):
        """Schedule automatic unblock after TTL."""
        await asyncio.sleep(ttl)
        if ip in self.blocked_ips:
            await self.unblock_ip(ip, actor="system")
    
    def get_status(self) -> Dict:
        """Get current blocked IPs and their unblock times."""
        now = asyncio.get_event_loop().time()
        return {
            ip: {"unblock_in": max(0, int(ts - now))}
            for ip, ts in self.blocked_ips.items()
        }
    
    def get_audit_log(self, limit: int = 100) -> List[AuditItem]:
        """Get recent audit entries."""
        return list(self.audit_log)[-limit:]
