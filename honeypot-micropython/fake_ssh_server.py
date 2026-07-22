import uasyncio as asyncio
import usocket as socket
import sys
from web_dashboard import log_attempt

async def start_fake_ssh():
    addr = socket.getaddrinfo("0.0.0.0", 22)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print("[*] SSH honeypot listening on port 22")
    while True:
        conn, client = s.accept()
        print(f"[!] SSH attempt from {client}")
        try:
            conn.send(b'SSH-2.0-OpenSSH_7.9p1\r\n')
            log_attempt('SSH', client[0])
        except Exception as e:
            print("SSH error:", e)
        finally:
            conn.close()
