import asyncio
from datetime import datetime
import sqlite3

# Initialize SQLite database for logging
def init_db():
    conn = sqlite3.connect("honeypot_logs.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY,
                        time TEXT,
                        service TEXT,
                        ip TEXT,
                        action TEXT)''')
    conn.commit()
    conn.close()

# Add log entry
def log_to_db(service, ip, action):
    conn = sqlite3.connect("honeypot_logs.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (time, service, ip, action) VALUES (?, ?, ?, ?)", (datetime.now(), service, ip, action))
    conn.commit()
    conn.close()

# SSH Honeypot as asyncio Protocol
class HoneypotSSHProtocol(asyncio.Protocol):
    def __init__(self, log_callback):
        self.log_callback = log_callback

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        self.ip = peername[0] if peername else "Unknown"
        self.transport = transport

        print(f"[+] Connection from {self.ip}")
        self.log_callback("SSH", self.ip, "Connection Made")
        self.transport.write(b"login: ")

    def data_received(self, data):
        message = data.decode('utf-8').strip()
        if message == "root" or message == "admin":
            self.transport.write(b"Password: ")
        elif message == "password":
            self.transport.write(b"Access granted\r\n")
            self.log_callback("SSH", self.ip, "Authorized")
        elif message == "exit":
            self.transport.write(b"Goodbye\r\n")
            self.transport.close()
            self.log_callback("SSH", self.ip, "Disconnected")
        else:
            self.transport.write(b"Unknown command\r\n")

async def fake_ssh_server():
    try:
        port = 8080
        print(f"[DEBUG] Attempting to bind SSH honeypot on port {port}")
        server = await asyncio.start_server(
            lambda: HoneypotSSHProtocol(log_to_db), host="127.0.0.1", port=port
        )
        print("[*] SSH Honeypot running on 127.0.0.1:%d" % port)
        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"[ERROR] Failed to start SSH Honeypot: {e}")

if __name__ == "__main__":
    init_db()
    asyncio.run(fake_ssh_server())