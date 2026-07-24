import geoip2.database
import requests
from flask import Flask, render_template_string, request
from datetime import datetime
import asyncio
import socket

app = Flask(__name__)
LOGGED_EVENTS = []

try:
    GEOIP_READER = geoip2.database.Reader('GeoLite2-City.mmdb')
except Exception:
    GEOIP_READER = None

def lookup_geoip(ip):
    if GEOIP_READER and ip and not ip.startswith('127.'):
        try:
            resp = GEOIP_READER.city(ip)
            country = resp.country.name or 'unknown'
            city = resp.city.name or 'unknown'
            return country, city
        except Exception:
            pass
    # fallback to an online API
    try:
        if ip and not ip.startswith('127.'):
            r = requests.get(f'https://ipapi.co/{ip}/json/', timeout=2)
            data = r.json()
            return data.get('country_name', 'unknown'), data.get('city', 'unknown')
    except Exception:
        pass
    return 'unknown', 'unknown'

def log_event(service, ip, extra=''):
    now = datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %Z')
    country, city = lookup_geoip(ip)
    LOGGED_EVENTS.append({'time': now, 'service': service, 'ip': ip, 'country': country, 'city': city, 'extra': extra})
    print(f"[{service}] {ip} ({country}, {city}): {extra}")

@app.route('/')
def dashboard():
    html = '''<html><head><title>Honeypot Dashboard</title></head><body><h1>Honeypot Logs</h1>'''
    html += '''<table border='1'><tr><th>Time</th><th>Service</th><th>IP</th><th>Country</th><th>City</th><th>Extra</th></tr>'''
    for log in LOGGED_EVENTS[-100:]:
        html += f"<tr><td>{log['time']}</td><td>{log['service']}</td><td>{log['ip']}</td><td>{log['country']}</td><td>{log['city']}</td><td>{log['extra']}</td></tr>"
    html += "</table></body></html>"
    return html

SSH_PORT = 2222
TELNET_PORT = 2323
FTP_PORT = 2121

FAKE_PROMPT = b"pi@raspberrypi:~$ "
FAKE_RESPONSES = {
    'ls': b"Desktop  Documents  Downloads  Music  Pictures  Public\n",
    'pwd': b"/home/pi\n",
    'whoami': b"pi\n",
    'id': b"uid=1000(pi) gid=1000(pi) groups=1000(pi)\n",
    'cat flag.txt': b"flag{honeypot_captured}\n",
    'uname -a': b"Linux raspberrypi 5.4.0-42-generic #1 SMP x86_64 GNU/Linux\n",
    'help': b"ls pwd whoami id cat flag.txt uname -a exit help\n",
}

def get_fake_response(cmd):
    return FAKE_RESPONSES.get(cmd, b"bash: command not found\n")

async def interactive_ssh(reader, writer):
    ip = writer.get_extra_info('peername')[0]
    log_event('SSH', ip, 'interactive connection')
    writer.write(b'SSH-2.0-OpenSSH_7.9p1 Debian-10\r\nlogin: ')
    await writer.drain()
    username = await reader.readline()
    writer.write(b'Password: ')
    await writer.drain()
    password = await reader.readline()
    log_event('SSH', ip, f'login={username.strip().decode(errors="ignore")}, password={password.strip().decode(errors="ignore")}')
    writer.write(b'\nWelcome to Ubuntu 20.04.6 LTS (GNU/Linux 5.4.0-42-generic x86_64)\n')
    writer.write(FAKE_PROMPT)
    await writer.drain()
    while True:
        line = await reader.readline()
        if not line:
            break
        cmd = line.decode().strip()
        log_event('SSH', ip, f'shell: {cmd}')
        if cmd == 'exit':
            writer.write(b'logout\nConnection closed by remote host.\n')
            await writer.drain()
            break
        writer.write(get_fake_response(cmd))
        writer.write(FAKE_PROMPT)
        await writer.drain()
    writer.close()
    await writer.wait_closed()

async def handle_banner(reader, writer, service):
    ip = writer.get_extra_info('peername')[0]
    log_event(service, ip)
    if service == 'Telnet':
        writer.write(b'Welcome to Telnet!\n')
    elif service == 'FTP':
        writer.write(b'220 (vsFTPd 3.0.3)\n')
    await writer.drain()
    writer.close()
    await writer.wait_closed()

async def start_servers():
    ssh = await asyncio.start_server(interactive_ssh, '0.0.0.0', SSH_PORT)
    telnet = await asyncio.start_server(
        lambda r, w: handle_banner(r, w, 'Telnet'), '0.0.0.0', TELNET_PORT)
    ftp = await asyncio.start_server(
        lambda r, w: handle_banner(r, w, 'FTP'), '0.0.0.0', FTP_PORT)

    print(f"SSH honeypot listening on 0.0.0.0:{SSH_PORT}")
    print(f"Telnet honeypot listening on 0.0.0.0:{TELNET_PORT}")
    print(f"FTP honeypot listening on 0.0.0.0:{FTP_PORT}")

    from threading import Thread
    def run_dashboard():
        app.run(host="0.0.0.0", port=5050)
    Thread(target=run_dashboard, daemon=True).start()

    async with ssh, telnet, ftp:
        await asyncio.gather(
            ssh.serve_forever(),
            telnet.serve_forever(),
            ftp.serve_forever()
        )

if __name__ == "__main__":
    asyncio.run(start_servers())
