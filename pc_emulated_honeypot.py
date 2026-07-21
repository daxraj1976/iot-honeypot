import asyncio
import socket
from datetime import datetime, timedelta
from flask import Flask, render_template_string
import requests
import sqlite3
import threading

# Flask Web Dashboard Setup
app = Flask(__name__)
db_path = "honeypot_logs.db"

# Initialize SQLite Database for Persistent Logs
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY,
                        time TEXT,
                        service TEXT,
                        ip TEXT,
                        country TEXT,
                        city TEXT)''')
    conn.commit()
    conn.close()

# Add a log to the SQLite Database
def log_to_db(service, ip, geo="Unknown, Unknown"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (time, service, ip, country, city) VALUES (?, ?, ?, ?, ?)",
                   (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), service, ip, *geo.split(", ")))
    conn.commit()
    conn.close()

# Fetch Geo-IP Location Info (IPInfo API)
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

# Log Attempt & Enrich with GeoData
def log_attempt(service, ip):
    geo_data = fetch_geo(ip)
    print(f"[+] Logged: {service} attempt from {ip} ({geo_data})")
    log_to_db(service, ip, geo_data)

@app.route('/')
def dashboard():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT time, service, ip, country, city FROM logs ORDER BY time DESC LIMIT 100")
    logs = cursor.fetchall()
    conn.close()

    log_html = "".join(
        f"<tr><td>{time}</td><td>{service}</td><td>{ip}</td><td>{country}</td><td>{city}</td></tr>"
        for (time, service, ip, country, city) in logs
    )
    html_template = f"""
    <!doctype html>
    <html>
        <head><title>Honeypot Dashboard</title></head>
        <body>
            <h1>Honeypot Logs</h1>
            <table border="1">
                <tr><th>Time</th><th>Service</th><th>IP</th><th>Country</th><th>City</th></tr>
                {log_html}
            </table>
        </body>
    </html>
    """
    return render_template_string(html_template)

async def fake_ssh_server():
    host, port = '127.0.0.1', 2222
    try:
        loop = asyncio.get_event_loop()
        server = await loop.create_server(
            lambda: HoneypotProtocol('SSH', log_attempt), host, port
        )
        print(f"[*] SSH honeypot listening on {host}:{port}")
        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"[ERROR] Failed to start SSH server: {e}")

async def fake_telnet_server():
    host, port = '127.0.0.1', 2323
    try:
        loop = asyncio.get_event_loop()
        server = await loop.create_server(
            lambda: HoneypotProtocol('Telnet', log_attempt), host, port
        )
        print(f"[*] Telnet honeypot listening on {host}:{port}")
        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"[ERROR] Failed to start Telnet server: {e}")

async def fake_ftp_server():
    host, port = '127.0.0.1', 2121
    try:
        loop = asyncio.get_event_loop()
        server = await loop.create_server(
            lambda: HoneypotProtocol('FTP', log_attempt), host, port
        )
        print(f"[*] FTP honeypot listening on {host}:{port}")
        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"[ERROR] Failed to start FTP server: {e}")

class HoneypotProtocol(asyncio.Protocol):
    def __init__(self, service, log_callback):
        self.service = service
        self.log_callback = log_callback

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        if peername:
            self.log_callback(self.service, peername[0])
        self.transport = transport
        self.transport.close()

async def main():
    tasks = [
        fake_ssh_server(),
        fake_telnet_server(),
        fake_ftp_server()
    ]
    await asyncio.gather(*tasks)

# Running Flask dashboard on a separate thread
def run_dashboard():
    app.run(host="0.0.0.0", port=5050, debug=False, threaded=True)

if __name__ == '__main__':
    init_db()
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[*] Server shutting down...")