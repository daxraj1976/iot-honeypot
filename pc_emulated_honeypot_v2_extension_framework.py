import asyncio
import socket
from datetime import datetime, timedelta
from flask import Flask, render_template_string
import requests
import sqlite3
import threading
import json
from random import choice

# Flask dashboard setup
app = Flask(__name__)
db_path = "honeypot_logs.db"

# SSH Commands to Simulate
ssh_fake_commands = {
    "ls": "backup  logs  config  secrets",
    "pwd": "/home/attacker",
    "cat secrets": "[ERROR] Permission Denied."
}

# Initialize SQLite database for storing logs
def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY,
                        time TEXT,
                        service TEXT,
                        ip TEXT,
                        country TEXT,
                        city TEXT,
                        extra TEXT)''')
    conn.commit()
    conn.close()

# Add a log to persistent storage
def log_to_db(service, ip, geo="Unknown, Unknown", extra=""):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (time, service, ip, country, city, extra) VALUES (?, ?, ?, ?, ?, ?)",
                   (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), service, ip, *geo.split(", "), json.dumps(extra)))
    conn.commit()
    conn.close()

# GeoIP Fetcher

def fetch_geo(ip):
    try:

         ....more_simulatedenroute!