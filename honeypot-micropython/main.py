# main.py for Pico W MicroPython Honeypot
import network
import uasyncio as asyncio
from fake_ssh_server import start_fake_ssh
from fake_telnet_server import start_fake_telnet
from fake_ftp_server import start_fake_ftp
from web_dashboard import run_dashboard

# EDIT HERE
WIFI_SSID = "YOUR_WIFI"
WIFI_PASSWORD = "YOUR_PASSWORD"

# Connect WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(WIFI_SSID, WIFI_PASSWORD)

import time
while not wlan.isconnected():
    print("Connecting to WiFi...")
    time.sleep(1)
print("Connected! IP:", wlan.ifconfig()[0])

async def main():
    print("[+] Starting honeypot servers on Pico W...")
    await asyncio.gather(
        start_fake_ssh(),
        start_fake_telnet(),
        start_fake_ftp(),
        run_dashboard()
    )

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("[!] Honeypot stopped.")
