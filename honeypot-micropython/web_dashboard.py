from microdot import Microdot, Response
import time

logs = []
app = Microdot()
Response.default_content_type = "text/html"

def log_attempt(service, ip):
    logs.append({"service": service, "ip": ip, "time": time.strftime("%Y-%m-%d %H:%M:%S")})
    print(f"[+] Logged: {service} attempt from {ip}")

@app.route('/')
def home(request):
    log_html = "".join(
        f"<tr><td>{log['time']}</td><td>{log['service']}</td><td>{log['ip']}</td></tr>"
        for log in logs
    )
    html = f"""
    <html>
    <head><title>Pico W Honeypot Dashboard</title></head>
    <body>
        <h1>Honeypot Logs</h1>
        <table border='1'><tr><th>Time (UTC)</th><th>Service</th><th>IP</th></tr>{log_html}</table>
        <p><b>Note:</b> Time is UTC and location is not available on Pico W. For GeoIP, use the PC version.</p>
    </body>
    </html>
    """
    return html

def start_dashboard():
    app.run(port=80)
