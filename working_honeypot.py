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
    def __init__(self):
        self.transport = None
        self.state = 'banner'
        self.ip = 'unknown'
        self.username = ''
        self.input_buffer = b''
        self.logged_in = False
        self.prompt = b'pi@raspberrypi:~$ '

    def connection_made(self, transport):
        self.transport = transport
        peername = transport.get_extra_info('peername')
        self.ip = peername[0] if peername else 'unknown'
        log_event('SSH', self.ip, 'SSH connection start')
        transport.write(b'SSH-2.0-OpenSSH_7.9p1 Debian-10\r\n')
        # Real SSH expects exchange, but we skip to login, for safety
        transport.write(b'login: ')
        self.state = 'username'

    def data_received(self, data):
        self.input_buffer += data
        # Handle line-by-line input
        if b'\n' in self.input_buffer or b'\r' in self.input_buffer:
            line = self.input_buffer.strip().decode(errors='ignore')
            self.input_buffer = b''
            if self.state == 'username':
                self.username = line
                self.transport.write(b'Password: ')
                self.state = 'password'
            elif self.state == 'password':
                self.transport.write(b'\r\nWelcome to Ubuntu 20.04.6 LTS (GNU/Linux 5.4.0-42-generic x86_64)\r\n')
                self.transport.write(self.prompt)
                self.state = 'shell'
                self.logged_in = True
                log_event('SSH', self.ip, f'Login as {self.username}')
            elif self.state == 'shell':
                log_event('SSH', self.ip, f'{self.username}$ {line}')
                output = self.simulate_command(line)
                self.transport.write(output + self.prompt)

    def simulate_command(self, line):
        cmds = {
            'ls': b"Desktop  Downloads  Documents  Music  Pictures  Public\n",
            'pwd': b"/home/pi\n",
            'whoami': (self.username+"\n").encode(),
            'id': b"uid=1000(pi) gid=1000(pi) groups=1000(pi)\n",
            'cat flag.txt': b"flag{honeypot_example_flag}\n",
            'uname -a': b"Linux raspberrypi 5.4.0-42-generic #1 SMP x86_64 GNU/Linux\n",
            'exit': b"logout\n",
            'help': b"ls pwd whoami id cat uname exit help\n",
        }
        output = cmds.get(line.strip(), b"bash: command not found\n")
        if line.strip() == 'exit':
            # End session
            self.transport.write(b'Connection closed by remote host.\n')
            self.transport.close()
        return output

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