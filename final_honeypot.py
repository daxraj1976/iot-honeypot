import asyncio
import sqlite3
from datetime import datetime
from flask import Flask, render_template_string
import requests
import threading
import json

# Flask app for dashboard
app = Flask(__name__)
DB_PATH = "honeypot.db"

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_PATH)
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

# Get geo-location for IP
def get_geo_location(ip):
    try:
        # Using a free ipinfo service
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                return data.get('country', 'Unknown'), data.get('city', 'Unknown')
    except Exception as e:
        print(f"Geo lookup failed for {ip}: {e}")
    return "Unknown", "Unknown"

# Log connection attempt
def log_attempt(service, ip, details=""):
    country, city = get_geo_location(ip)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO logs (timestamp, service, ip, country, city, details) VALUES (?, ?, ?, ?, ?, ?)",
              (datetime.now().isoformat(), service, ip, country, city, details))
    conn.commit()
    conn.close()
    print(f"[LOG] {service} attempt from {ip} ({city}, {country}) - {details}")

# SSH Honeypot Protocol
class SSHHoneypot(asyncio.Protocol):
    def __init__(self):
        self.state = 'USERNAME'
        self.username = None
        
    def connection_made(self, transport):
        self.transport = transport
        peername = transport.get_extra_info('peername')
        self.ip = peername[0] if peername else 'unknown'
        print(f"SSH connection from {self.ip}")
        self.transport.write(b'SSH-2.0-OpenSSH_7.9p1 Ubuntu-10\r\n')
        
    def data_received(self, data):
        try:
            message = data.decode('utf-8', errors='ignore').strip()
            if self.state == 'USERNAME':
                self.username = message
                self.log_attempt('SSH_LOGIN_ATTEMPT', f'username: {self.username}')
                self.transport.write(b'Password: ')
                self.state = 'PASSWORD'
            elif self.state == 'PASSWORD':
                password = message
                self.log_attempt('SSH_LOGIN_ATTEMPT', f'username: {self.username}, password: {password}')
                self.transport.write(b'Access denied\r\n')
                self.transport.write(b'Last login: ')
                self.transport.write(str(datetime.now()).encode())
                self.transport.write(b' from ')
                self.transport.write(self.ip.encode())
                self.transport.write(b'\r\n$ ')
                self.state = 'COMMAND'
            elif self.state == 'COMMAND':
                if message in ['exit', 'quit', 'logout']:
                    self.transport.write(b'Connection to localhost closed.\r\n')
                    self.transport.close()
                    return
                elif message == 'ls':
                    self.transport.write(b'Documents  Downloads  Music  Pictures  Public  Templates  Videos\r\n')
                elif message == 'pwd':
                    self.transport.write(b'/home/user\r\n')
                elif message == 'whoami':
                    self.transport.write(b'user\r\n')
                elif message == 'id':
                    self.transport.write(b'uid=1000(user) gid=1000(user) groups=1000(user)\r\n')
                elif message.startswith('cat ') or message.startswith('more ') or message.startswith('less '):
                    self.transport.write(b'cat: No such file or directory\r\n')
                elif message == '':
                    pass  # Empty command, just show prompt
                else:
                    self.transport.write(f'{message}: command not found\r\n'.encode())
                self.transport.write(b'$ ')
        except Exception as e:
            print(f"Error in SSH handler: {e}")
            self.transport.close()
            
    def connection_lost(self, exc):
        print(f"SSH connection from {self.ip} closed")
        
    def log_attempt(self, action, details):
        log_attempt('SSH', self.ip, f"{action}: {details}")

# Telnet Honeypot Protocol  
class TelnetHoneypot(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        peername = transport.get_extra_info('peername')
        self.ip = peername[0] if peername else 'unknown'
        print(f"Telnet connection from {self.ip}")
        self.transport.write(b'Ubuntu 20.04.5 LTS\r\n')
        self.transport.write(b'localhost login: ')
        
    def data_received(self, data):
        try:
            message = data.decode('utf-8', errors='ignore').strip()
            if 'login:' in self.transport.get_extra_info('peername', ''):
                # Simplified - just log the attempt
                self.log_attempt('TELNET_LOGIN', f'attempt: {message}')
                self.transport.write(b'Password: ')
            else:
                self.log_attempt('TELNET_COMMAND', f'command: {message}')
                if message in ['exit', 'quit']:
                    self.transport.write(b'Connection closed.\r\n')
                    self.transport.close()
                elif message == 'ls':
                    self.transport.write(b'file1.txt  file2.log  script.sh\r\n')
                elif message == 'pwd':
                    self.transport.write(b'/home/user\r\n')
                else:
                    self.transport.write(b'Command not found\r\n')
                self.transport.write(b'\r\n')
        except Exception as e:
            print(f"Error in Telnet handler: {e}")
            self.transport.close()
            
    def connection_lost(self, exc):
        print(f"Telnet connection from {self.ip} closed")
        
    def log_attempt(self, action, details):
        log_attempt('TELNET', self.ip, f"{action}: {details}")

# FTP Honeypot Protocol
class FTPHandler(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        peername = transport.get_extra_info('peername')
        self.ip = peername[0] if peername else 'unknown'
        print(f"FTP connection from {self.ip}")
        self.transport.write(b'220 (vsFTPd 3.0.3)\r\n')
        
    def data_received(self, data):
        try:
            message = data.decode('utf-8', errors='ignore').strip()
            self.log_attempt('FTP_COMMAND', f'command: {message}')
            if message.upper() == 'USER':
                self.transport.write(b'331 Please specify the password.\r\n')
            elif message.upper() == 'PASS':
                self.transport.write(b'530 Login incorrect.\r\n')
            elif message.upper() == 'QUIT':
                self.transport.write(b'221 Goodbye.\r\n')
                self.transport.close()
            elif message.upper() in ['LIST', 'NLST']:
                self.transport.write(b'150 Here comes the directory listing.\r\n')
                self.transport.write(b'226 Directory send OK.\r\n')
            elif message.upper() == 'PWD':
                self.transport.write(b'257 "/" is the current directory\r\n')
            else:
                self.transport.write(b'500 Unknown command.\r\n')
        except Exception as e:
            print(f"Error in FTP handler: {e}")
            self.transport.close()
            
    def connection_lost(self, exc):
        print(f"FTP connection from {self.ip} closed")
        
    def log_attempt(self, action, details):
        log_attempt('FTP', self.ip, f"{action}: {details}")

# HTTP Honeypot - Simple fake web server
async def handle_http(reader, writer):
    try:
        request = await reader.readline()
        method, path, version = request.decode().split()
        print(f"HTTP request: {method} {path} from {writer.get_extra_info('peername')[0]}")
        # Log the request
        log_attempt('HTTP', writer.get_extra_info('peername')[0], f'{method} {path}')
        
        # Simple response
        response = '''HTTP/1.1 200 OK
Content-Type: text/html
Connection: close

<html>
<head><title>Welcome</title></head>
<body>
<h1>Welcome to nginx!</h1>
<p>If you see this page, the nginx web server is successfully installed and working.</p>
</body>
</html>'''
        writer.write(response.encode())
        await writer.drain()
    except Exception as e:
        print(f"HTTP error: {e}")
    finally:
        writer.close()
        await writer.wait_closed()

# Start all servers
async def start_servers():
    # SSH on port 2222
    ssh_server = await asyncio.start_server(
        SSHHoneypot, '0.0.0.0', 2222)
    print(f'SSH honeypot listening on {ssh_server.sockets[0].getsockname()}')
    
    # Telnet on port 2323
    telnet_server = await asyncio.start_server(
        TelnetHoneypot, '0.0.0.0', 2323)
    print(f'Telnet honeypot listening on {telnet_server.sockets[0].getsockname()}')
    
    # FTP on port 2121
    ftp_server = await asyncio.start_server(
        FTPHandler, '0.0.0.0', 2121)
    print(f'FTP honeypot listening on {ftp_server.sockets[0].getsockname()}')
    
    # HTTP on port 8080
    http_server = await asyncio.start_server(
        handle_http, '0.0.0.0', 8080)
    print(f'HTTP honeypot listening on {http_server.sockets[0].getsockname()}')
    
    # Wait for all servers
    await asyncio.gather(
        ssh_server.serve_forever(),
        telnet_server.serve_forever(),
        ftp_server.serve_forever(),
        http_server.serve_forever()
    )

# Flask routes
@app.route('/')
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT timestamp, service, ip, country, city, details 
                 FROM logs ORDER BY timestamp DESC LIMIT 100''')
    logs = c.fetchall()
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
    for log in logs:
        html += f'<tr><td>{log[0]}</td><td>{log[1]}</td><td>{log[2]}</td><td>{log[3]}</td><td>{log[4]}</td><td>{log[5]}</td></tr>'
    html += '''
        </table>
    </body>
    </html>
    '''
    return html

def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Start Flask in a thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    print('Flask dashboard started on http://0.0.0.0:5000')
    
    # Start all honeypot servers
    try:
        asyncio.run(start_servers())
    except KeyboardInterrupt:
        print('Shutting down honeypot...')