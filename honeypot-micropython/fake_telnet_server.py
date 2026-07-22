import uasyncio as asyncio
import usocket as socket
from web_dashboard import log_attempt

async def start_fake_telnet():
    addr = socket.getaddrinfo("0.0.0.0", 23)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print("[*] Telnet honeypot listening on port 23")
    while True:
        conn, client = s.accept()
        print(f"[!] Telnet attempt from {client}")
        try:
            conn.send(b'Welcome to Telnet!\n')
            log_attempt('Telnet', client[0])
        except Exception as e:
            print("Telnet error:", e)
        finally:
            conn.close()
