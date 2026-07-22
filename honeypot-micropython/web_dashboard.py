from microdot import Microdot, Response
import time

logs = []
app = Microdot()
Response.default_content_type = "text/html"

def log_attempt(service, ip):
    logs.append({"service": service, "ip": ip, "time": time.strftime('%Y-%m-%d %H:%M:%S')})
    print(f"[LOG] {service} attempt from {ip}")

@app.route('/')
def home(request):
    log_html = "".join(
        f"<tr><td>{log['time']}</td><td>{log['service']}</td><td>{log['ip']}</td></tr>"
        for log in logs[-100:]
    )
    html = f"""
    <html>
    <head><title>Pico Honeypot Dashboard</title></head>
    <body>
        <h1>Pico Honeypot Logs</h1>
        <table border='1'><tr><th>Time</th><th>Service</th><th>IP</th></tr>{log_html}</table>
    </body>
    </html>
    """
    return html

def run_dashboard():
    app.run(host='0.0.0.0', port=80)
