import uasyncio as asyncio
from fake_ssh_server import start_fake_ssh
from fake_telnet_server import start_fake_telnet
from fake_ftp_server import start_fake_ftp
from web_dashboard import start_dashboard
import gc

async def main():
    # Run all servers concurrently
    print("[*] Starting Honeypot Services...")
    await asyncio.gather(
        start_fake_ssh(),
        start_fake_telnet(),
        start_fake_ftp(),
        start_dashboard()
    )

    
gc.collect()  # Memory cleanup (important for Pico)
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\n[*] Honeypot shutting down gracefully...")