from microdot import Microdot, Response
from datetime import datetime

app = Microdot()
Response.default_content_type = "text/html"
logs = []

@app.route('/')
def home(request):
    log_html = "".join(
        f"<tr><td>{log['time']}</td><td>{log['service']}</td><td>{log['ip']}</td></tr>"
        for log in logs
    )
    html = f"""
    <html>
    <head><title>Honeypot Dashboard</title></head>
    <body>
        <h1>Honeypot Logs</h1>
        <table border="1">
            <tr><th>Time</th><th>Service</th><th>IP</th></tr>
            {log_html}
        </table>
    </body>
    </html>
    """
    return html

def log_attempt(service, ip):
    logs.append({"service": service, "ip": ip, "time": str(datetime.now())})
    print(f"[+] Logged: {service} attempt from {ip}")

def start_dashboard():
    app.run(port=80)