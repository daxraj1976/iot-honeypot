import geoip2.database
import requests
from flask import Flask, render_template_string, request
from datetime import datetime

app = Flask(__name__)
LOGGED_EVENTS = []

try:
    GEOIP_READER = geoip2.database.Reader('GeoLite2-City.mmdb')
except Exception:
    GEOIP_READER = None

# ...rest of your code...

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

# ...rest of your code...

# Update dashboard HTML accordingly to show new columns, e.g. Country, City, Time (with tz).
