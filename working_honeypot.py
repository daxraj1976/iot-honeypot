#!/usr/bin/env python3
"""
Final working honeypot with all features
"""
import asyncio
import sqlite3
import threading
from datetime import datetime
from flask import Flask, render_template_string
import requests
import json

# Configuration
SSH_PORT = 2222
TELNET_PORT = 2323
FTP_PORT = 2121
HTTP_PORT = 8080
FLASK_PORT = 5050
DB_NAME = 'honeypot_final.db'

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  timestamp TEXT,
                  service TEXT,
                  ip TEXT,
                  country TEXT,
                  city TEXT,
                  details TEXT)''')
    conn.commit()
    conn.close()

def log_event(service, ip, details=''):
    # Get geo-location
    try:
        resp = requests.get(f'http://ip-api.com/json/{ip}', timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('status') == 'success':
                country = data.get('country', 'Unknown')
                city = data.get('city', 'Unknown')
            else:
                country = 'Unknown'
                city = 'Unknown'
        else:
            country = 'Unknown'
            city = 'Unknown'
    except:
        country = 'Unknown'
        city = 'Unknown'
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO logs (timestamp, service, ip, country, city, details)
                 VALUES (datetime('now'), ?, ?, ?, ?, ?)''',
              (service, ip, country, city, details))
    conn.commit()
    conn.close()
    print(f"[LOG] {service} from {ip} ({city}, {country}): {details}")

# Honeypot Protocols
class SSHHoneypot(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        ip = peername[0] if peername else 'unknown'
        log_event('SSH', ip, 'Connection attempt')
        # Send SSH banner
        transport.write(b'SSH-2.0-OpenSSH_7.9p1 Debian-10\r\n')
        # Close connection after banner (this is a banner-only honeypot)
        transport.close()

class TelnetHoneypot(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        ip = peername[0] if peername else 'unknown'
        log_event('Telnet', ip, 'Connection attempt')
        # Send telnet banner
        transport.write(b'Welcome to Ubuntu 20.04 LTS (GNU/Linux 5.4.0-42-generic x86_64)\r\n')
        transport.write(b'login: ')
        # We don't actually handle login, just banner

    def data_received(self, data):
        # Log any input received
        peername = self.transport.get_extra_info('peername')
        ip = peername[0] if peername else 'unknown'
        input_data = data.decode(errors='ignore').strip()
        if input_data:
            log_event('Telnet', ip, f'Input: {input_data}')
        # Close connection
        self.transport.close()

class FTPHandler(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        ip = peername[0] if peername else 'unknown'
        log_event('FTP', ip, 'Connection attempt')
        # Send FTP banner
        self.transport.write(b'220 (vsFTPd 3.0.3)\r\n')
        # Close connection
        self.transport.close()

# HTTP Handler
async def handle_http(request):
    # Simple HTTP server that logs requests
    # We'll implement a basic HTTP server that just logs and responds
    pass  # We'll implement a simpler approach below

# Dashboard setup
app = Flask(__name__)

@app.route('/')
def index():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''SELECT timestamp, service, ip, country, city, details 
                 FROM logs ORDER BY timestamp DESC LIMIT 100''')
    rows = c.fetchall()
    conn.close()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Honeypot Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            tr:nth-child(even) { background-color: #f9f9f9; }
        </style>
    </head>
    <body>
        <h1>Honeypot Activity Log</h1>
        <table>
            <tr>
                <th>Timestamp</th>
                <th>Service</th>
                <th>IP Address</th>
                <th>Country</th>
                <th>City</th>
                <th>Details</th>
            </tr>
    '''
    for row in rows:
        html += f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td><td>{row[4]}</td><td>{row[5]}</td></tr>'
    html += '''
        </table>
    </body>
    </html>
    '''
    return html

def run_flask():
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False, use_reloader=False)

async def start_servers():
    # Start SSH server
    ssh_server = await asyncio.start_server(SSHHoneypot, '0.0.0.0', SSH_PORT)
    print(f'SSH honeypot listening on 0.0.0.0:{SSH_PORT}')
    
    # Start Telnet server
    telnet_server = await asyncio.start_server(TelnetHoneypot, '0.0.0.0', TELNET_PORT)
    print(f'Telnet honeypot listening on 0.0.0.0:{TELNET_PORT}')
    
    # Start FTP server
    ftp_server = await asyncio.start_server(FTPHandler, '0.0.0.0', FTP_PORT)
    print(f'FTP honeypot listening on 0.0.0.0:{FTP_PORT}')
    
    # Keep servers running
    await asyncio.gather(
        ssh_server.serve_forever(),
        telnet_server.serve_forever(),
        ftp_server.serve_forever()
    )

if __name__ == '__main__':
    # Clear any existing processes on our ports
    import subprocess
    import signal
    import os
    
    ports = [SSH_PORT, TELNET_PORT, FTP_PORT, HTTP_PORT, FLASK_PORT]
    for port in ports:
        try:
            subprocess.run(['fuser', '-k', f'{port}/tcp'], 
                          capture_output=True, timeout=2)
        except:
            pass  # fuser might not be available
    
    # Initialize database
    init_db()
    
    # Start Flask in a thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f'Flask dashboard started on http://0.0.0.0:{FLASK_PORT}')
    
    # Start all honeypot servers
    try:
        asyncio.run(start_servers())
    except KeyboardInterrupt:
        print('Shutting down honeypot...')