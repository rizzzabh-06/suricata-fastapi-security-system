import asyncio
import json
import os
from typing import Callable, Optional
import aiofiles

class EVEWatcher:
    """Async tailer for Suricata EVE JSON log.
    Config: EVE_PATH env var or default /var/log/suricata/eve.json
    """
    def __init__(self, path: Optional[str] = None, on_event: Optional[Callable] = None):
        self.path = path or os.getenv("EVE_PATH", "/var/log/suricata/eve.json")
        self.on_event = on_event
        self.running = False

    async def start(self):
        self.running = True
        retry_delay = 1
        
        while self.running:
            try:
                async with aiofiles.open(self.path, mode='r') as f:
                    await f.seek(0, 2)  # Seek to end
                    retry_delay = 1
                    
                    while self.running:
                        line = await f.readline()
                        if line:
                            line = line.strip()
                            if line:
                                try:
                                    obj = json.loads(line)
                                    if self.on_event:
                                        await self.on_event(obj)
                                except json.JSONDecodeError:
                                    pass
                        else:
                            await asyncio.sleep(0.1)
            except FileNotFoundError:
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)
            except Exception:
                await asyncio.sleep(1)

    def stop(self):
        self.running = False
