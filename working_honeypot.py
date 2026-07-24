import geoip2.database
import requests
from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit
from datetime import datetime
import asyncio
import socket

app = Flask(__name__)
socketio = SocketIO(app, async_mode='threading')
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
    log = {'time': now, 'service': service, 'ip': ip, 'country': country, 'city': city, 'extra': extra}
    LOGGED_EVENTS.append(log)
    print(f"[{service}] {ip} ({country}, {city}): {extra}")
    socketio.emit('new_log', log)

@app.route('/')
def dashboard():
    return render_template_string('''
<html><head><title>Honeypot Dashboard</title></head><body>
<h1>Honeypot Logs (realtime)</h1>
<table id="logtable" border='1'><tr><th>Time</th><th>Service</th><th>IP</th><th>Country</th><th>City</th><th>Extra</th></tr>
{% for log in logs %}<tr><td>{{log.time}}</td><td>{{log.service}}</td><td>{{log.ip}}</td><td>{{log.country}}</td><td>{{log.city}}</td><td>{{log.extra}}</td></tr>{% endfor %}
</table>
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.5/socket.io.min.js"></script>
<script>
  var socket = io();
  socket.on('new_log', function(log) {
    var row = document.createElement('tr');
    [log.time, log.service, log.ip, log.country, log.city, log.extra].forEach(function(txt) {
      var td = document.createElement('td');
      td.textContent = txt;
      row.appendChild(td);
    });
    document.getElementById('logtable').appendChild(row);
    window.scrollTo(0, document.body.scrollHeight);
  });
</script>
</body></html>
''', logs=LOGGED_EVENTS[-100:])

SSH_PORT = 2222
TELNET_PORT = 2323
FTP_PORT = 2121

import shlex

class FakeShellSession:
    def __init__(self, username="pi"):
        self.username = username
        self.cwd = "/home/" + username
        self.fs = {
            "/home/"+username: ["Desktop", "Downloads", "Documents", "flag.txt"],
            "/home/"+username+"/Desktop": [],
            "/home/"+username+"/Downloads": [],
            "/home/"+username+"/Documents": [],
        }
        self.files = {"/home/"+username+"/flag.txt": "flag{honeypot_captured}"}
        self.history = []
    def prompt(self):
        return f"{self.username}@raspberrypi:{self.cwd.replace('/home/'+self.username, '~') if self.cwd.startswith('/home/'+self.username) else self.cwd}$ ".encode()
    def handle_command(self, cmd):
        self.history.append(cmd)
        args = shlex.split(cmd)
        if not args:
            return b""
        c = args[0]
        # Directory commands
        if c == "ls":
            return ("  ".join(self.fs.get(self.cwd, [])) + "\n").encode()
        elif c == "pwd":
            return (self.cwd+"\n").encode()
        elif c == "cd":
            if len(args) < 2:
                return b""
            target = args[1]
            if target == "..":
                if self.cwd.count("/") > 2:
                    self.cwd = "/".join(self.cwd.rstrip("/").split("/")[:-1])
                return b""
            elif target.startswith("/") and target in self.fs:
                self.cwd = target
                return b""
            else:
                path = self.cwd + "/" + target if not target.startswith("/") else target
                if path in self.fs:
                    self.cwd = path
                    return b""
                else:
                    return f"bash: cd: {target}: No such file or directory\n".encode()
        elif c == "touch" and len(args) > 1:
            for fname in args[1:]:
                if fname in self.fs.get(self.cwd, []):
                    continue
                self.fs[self.cwd].append(fname)
                self.files[self.cwd+"/"+fname] = ""
            return b""
        elif c == "rm" and len(args) > 1:
            for fname in args[1:]:
                try:
                    self.fs[self.cwd].remove(fname)
                    self.files.pop(self.cwd+"/"+fname, None)
                except Exception:
                    return f"rm: cannot remove '{fname}': No such file or directory\n".encode()
            return b""
        elif c == "cat" and len(args) > 1:
            fname = args[1]
            content = self.files.get(self.cwd+"/"+fname)
            if content is not None:
                return (content+"\n").encode()
            else:
                return f"cat: {fname}: No such file or directory\n".encode()
        elif c == "echo" and len(args) > 1:
            text = " ".join(args[1:])
            return (text+"\n").encode()
        elif c == "history":
            resp = "\n".join(f"{i+1}  {h}" for i, h in enumerate(self.history)) + "\n"
            return resp.encode()
        elif c == "help":
            return b"ls pwd cd touch rm cat echo history help exit\n"
        elif c == "exit":
            return b""
        return f"bash: {args[0]}: command not found\n".encode()

async def interactive_ssh(reader, writer):
    ip = writer.get_extra_info('peername')[0]
    writer.write(b'SSH-2.0-OpenSSH_7.9p1 Debian-10\r\nlogin: ')
    await writer.drain()
    username = await reader.readline()
    username = username.strip().decode(errors="ignore") or "pi"
    writer.write(b'Password: ')
    await writer.drain()
    password = await reader.readline()
    log_event('SSH', ip, f'login={username}, password={password.strip().decode(errors="ignore")}')
    writer.write(b'\nWelcome to Ubuntu 20.04.6 LTS (GNU/Linux 5.4.0-42-generic x86_64)\n')
    shell = FakeShellSession(username)
    writer.write(shell.prompt())
    await writer.drain()
    while True:
        line = await reader.readline()
        if not line:
            break
        cmd = line.decode().strip()
        log_event('SSH', ip, f'shell: {cmd}')
        if cmd == "exit":
            writer.write(b'logout\nConnection closed by remote host.\n')
            await writer.drain()
            break
        resp = shell.handle_command(cmd)
        writer.write(resp)
        writer.write(shell.prompt())
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
        socketio.run(app, host="0.0.0.0", port=5050)
    Thread(target=run_dashboard, daemon=True).start()

    async with ssh, telnet, ftp:
        await asyncio.gather(
            ssh.serve_forever(),
            telnet.serve_forever(),
            ftp.serve_forever()
        )

if __name__ == "__main__":
    asyncio.run(start_servers())
