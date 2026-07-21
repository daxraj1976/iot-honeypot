import asyncio
import threading
import socket
from datetime import datetime
import sqlitep
from flask import Flask, render_template_string
import requests

# Configuration
SSH_PORT = 2222
TELNET_PORT = 2323
FTP_PORT = 2121
HTTP_PORT = 8080
FLASK_PORT = 5050

# Database setup
DB_NAME = 'honeypot.db'

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
        resp = requests.get(f'http://ip-api.com/json/{ip}').json()
        country = resp.get('country', 'Unknown')
        city = resp.get('city', 'Unknown')
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

# Honeypot implementations
class SSHHoneypot(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        ip = peername[0] if peername else 'unknown'
        log_event('SSH', ip, 'Connection attempt')
        transport.write(b'SSH-2.0-OpenSSH_7.9p1 Debian-10\r\n')
        # We don't actually handle login, just banner

class TelnetHoneypot(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        ip = peername[0] if peername else 'unknown'
        log_event('Telnet', ip, 'Connection attempt')
        transport.write(b'Welcome to Ubuntu 20.04 LTS (GNU/Linux 5.4.0-42-generic x86_64)\r\n')
        transport.write(b'login: ')

    def data_received(self, data):
        peername = self.transport.get_extra_info('peername')
        ip = peername[0] if peername else 'unknown'
        # Just log any input
        log_event('Telnet', ip, f'Input: {data.decode(errors="ignore").strip()}')
        self.transport.write(b'Login incorrect\r\nlogin: ')

class FTPHandler(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        ip = peername[0] if peername else 'unknown'
        log_event('FTP', ip, 'Connection attempt')
        self.transport.write(b'220 (vsFTPd 3.0.3)\r\n')

    def data_received(self, data):
        peername = self.transport.get_extra_info('peername')
        ip = peername[0] if peername else 'unknown'
        cmd = data.decode(errors='ignore').strip().upper()
        log_event('FTP', ip, f'Command: {cmd}')
        if cmd.startswith('USER'):
            self.transport.write(b'331 Please specify the password.\r\n')
        elif cmd.startswith('PASS'):
            self.transport.write(b'530 Login incorrect.\r\n')
        elif cmd in ['QUIT', 'EXIT']:
            self.transport.write(b'221 Goodbye.\r\n')
            self.transport.close()
        else:
            self.transport.write(b'500 Unknown command.\r\n')

async def handle_http(request):
    # Simple HTTP server that logs requests
    # We'll use aiohttp for this, but for simplicity let's use a raw socket approach
    # Actually, let's use a different approach: we'll create a simple HTTP server with asyncio
    pass  # We'll implement this later if needed

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
    init_db()
    # Start Flask in a thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print(f'Flask dashboard running on http://0.0.0.0:{FLASK_PORT}')
    
    # Start the honeypot servers
    try:
        asyncio.run(start_servers())
    except KeyboardInterrupt:
        print('Shutting down...')