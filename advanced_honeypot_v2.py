import asyncio
from datetime import datetime
from flask import Flask, render_template_string
import sqlite3

# Flask dashboard setup
app = Flask(__name__)
db_path = "honeypot_logs.db"

# Initialize SQLite database for storing logs
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY,
                        time TEXT,
                        service TEXT,
                        ip TEXT,
                        action TEXT)''')
    conn.commit()
    conn.close()

# Add a log to persistent storage
def log_to_db(service, ip, action):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (time, service, ip, action) VALUES (?, ?, ?, ?)",
                   (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), service, ip, action))
    conn.commit()
    conn.close()

# SSH Protocol Simulation
class HoneypotSSHProtocol(asyncio.Protocol):
    def __init__(self, log_callback):
        self.log_callback = log_callback

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        self.ip = peername[0] if peername else "Unknown"
        self.transport = transport
        self.log_callback("SSH", self.ip, "Connection Made")
        self.transport.write(b"login: ")

    def data_received(self, data):
        message = data.decode('utf-8').strip()
        if message == "root" or message == "admin":
            self.transport.write(b"Password: ")
        elif message == "password" or message == "1234":
            self.transport.write(b"Access Granted\r\n$ ls\r\n")
            self.transport.write(b"files documents logs\r\n$ ")
            self.log_callback("SSH", self.ip, "Executed 'ls'")
        elif message == "exit":
            self.transport.write(b"Goodbye!\r\n")
            self.transport.close()
            self.log_callback("SSH", self.ip, "Disconnected")
        else:
            self.transport.write(b"Invalid command.\r\n$ ")

# SSH Server Coroutine
async def fake_ssh_server():
    host, port = '127.0.0.1', 2222
    loop = asyncio.get_event_loop()
    server = await loop.create_server(lambda: HoneypotSSHProtocol(log_to_db), host, port)
    print(f"[*] SSH honeypot listening on {host}:{port}")
    async with server:
        await server.serve_forever()

# Flask Dashboard
@app.route('/')
def dashboard():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT time, service, ip, action FROM logs ORDER BY time DESC LIMIT 100")
    logs = cursor.fetchall()
    conn.close()

    log_html = "".join(
        f"<tr><td>{time}</td><td>{service}</td><td>{ip}</td><td>{action}</td></tr>"
        for (time, service, ip, action) in logs
    )
    return f"""
    <!doctype html>
    <html>
        <head><title>Advanced Honeypot Dashboard</title></head>
        <body>
            <h1>Honeypot Logs</h1>
            <table border="1">
                <tr><th>Time</th><th>Service</th><th>IP</th><th>Action</th></tr>
                {log_html}
            </table>
        </body>
    </html>
    """

# Main Coroutine
async def main():
    await fake_ssh_server()

# Run the dashboard on a separate thread
def run_dashboard():
    app.run(host="0.0.0.0", port=5050, debug=False, threaded=True)

if __name__ == '__main__':
    init_db()
    import threading
    threading.Thread(target=run_dashboard, daemon=True).start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("[+] Shutting down...")