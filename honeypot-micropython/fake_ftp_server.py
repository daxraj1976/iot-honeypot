import uasyncio as asyncio
import usocket as socket
from web_dashboard import log_attempt

async def start_fake_ftp():
    addr = socket.getaddrinfo("0.0.0.0", 21)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print("[*] FTP honeypot listening on port 21")
    while True:
        conn, client = s.accept()
        print(f"[!] FTP attempt from {client}")
        try:
            conn.send(b'220 (vsFTPd 3.0.3)\n')
            log_attempt('FTP', client[0])
        except Exception as e:
            print("FTP error:", e)
        finally:
            conn.close()
