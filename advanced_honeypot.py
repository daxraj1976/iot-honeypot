import asyncio
import socket
from datetime import datetime, timedelta
from flask import Flask, render_template_string
import requests
import sqlite3
import threading
import json
from random import choice

# Flask dashboard setup
app = Flask(__name__)
db_path = "honeypot_logs.db"

# SSH Commands to Simulate
ssh_fake_commands = {
    "ls": "backup  logs  config  secrets",
    "pwd": "/home/attacker",
    "cat secrets": "[ERROR] Permission Denied.",
    "exit": "[INFO] Disconnecting from server..."
}

# Initialize SQLite database for storing logs
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY,
                        time TEXT,
                        service TEXT,
                        ip TEXT,
                        country TEXT,
                        city TEXT,
                        extra TEXT)''')
    conn.commit()
    conn.close()

# Add a log to persistent storage
def log_to_db(service, ip, geo="Unknown, Unknown", extra=""):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (time, service, ip, country, city, extra) VALUES (?, ?, ?, ?, ?, ?)",
                   (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), service, ip, *geo.split(", "), json.dumps(extra)))
    conn.commit()
    conn.close()

# GeoIP Fetcher
def fetch_geo(ip):
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        if response.status_code == 200:
            data = response.json()
            country = data.get("country", "Unknown")
            city = data.get("city", "Unknown")
            return f"{country}, {city}"
    except Exception as e:
        print(f"[WARNING] Failed Geo-IP lookup for {ip}: {e}")
    return "Unknown, Unknown"

# Interactive SSH Simulation
class HoneypotSSHProtocol(asyncio.Protocol):
    def __init__(self, log_callback):
        self.log_callback = log_callback

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        self.ip = peername[0] if peername else "Unknown"
        self.transport = transport
        print(f"[+] SSH connection from {self.ip}")
        self.transport.write(b"login: ")

    def data_received(self, data):
        message = data.decode('utf-8').strip()
        if message == "root" or message == "admin":
            self.transport.write(b"Password: ")
        elif message == "password" or message == "1234":
            self.transport.write(b"Welcome to the fake SSH server!\r\n$ ls\r\n")
            self.log_callback("SSH", self.ip, extra={"interaction": "ls"})
            self.transport.write(ssh_fake_commands["ls"].encode() + b"\r\n$ ")
        elif message in ssh_fake_commands:
            response = ssh_fake_commands[message]
            self.transport.write(response.encode() + b"\r\n$ ")
            self.log_callback("SSH", self.ip, extra={"interaction": message})
        elif message == "exit":
            self.transport.write(b"Goodbye!\r\n")
            self.transport.close()
        else:
            self.transport.write(b"Invalid command.\r\n$ ")

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
    cursor.execute("SELECT time, service, ip, country, city, extra FROM logs ORDER BY time DESC LIMIT 100")
    logs = cursor.fetchall()
    conn.close()

    log_html = "".join(
        f"<tr><td>{time}</td><td>{service}</td><td>{ip}</td><td>{country}</td><td>{city}</td><td>{json.loads(extra) if extra else ''}</td></tr>"
        for (time, service, ip, country, city, extra) in logs
    )
    html_template = f"""
    <!doctype html>
    <html>
        <head><title>Advanced Honeypot Dashboard</title></head>
        <body>
            <h1>Honeypot Logs</h1>
            <table border="1">
                <tr><th>Time</th><th>Service</th><th>IP</th><th>Country</th><th>City</th><th>Extra</th></tr>
                {log_html}
            </table>
        </body>
    </html>
    """
    return render_template_string(html_template)

async def main():
    tasks = [fake_ssh_server()]
    await asyncio.gather(*tasks)

# Run the dashboard on a separate thread
def run_dashboard():
    app.run(host="0.0.0.0", port=5050)

if __name__ == '__main__':
    init_db()
    threading.Thread(target=run_dashboard, daemon=True).start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Shutting down...")