# Smart IoT Honeypot

A safe, realistic SSH/Telnet/FTP honeypot for research or teaching—targeted for Linux (Python 3) or Raspberry Pi Pico W (MicroPython).

---

## Features
- **SSH/Telnet/FTP fake servers** (banner only for Telnet/FTP, realistic *interactive* fake SSH shell)
- **SQLite logging** with timestamps, IP, service, geo-info (Linux version)
- **Web dashboard** (Flask, Linux version) to view attacks live at `http://localhost:5050`

---

## Quick Start (Linux / Pi)

1. Clone the repo and enter the folder:
    ```bash
    git clone https://github.com/daxraj1976/iot-honeypot.git
    cd iot-honeypot
    ```
2. Install deps:
    ```bash
    sudo apt install python3 python3-pip
    pip3 install flask requests
    ```
3. Run it:
    ```bash
    python3 working_honeypot.py
    ```
4. Check the dashboard: [http://localhost:5050](http://localhost:5050)

---

## SSH "Interactive" Honeypot (Linux version)
- Connect on port 2222 (e.g. `ssh <your-ip> -p 2222`)
- Login prompt with username/password
- After login, a fake bash prompt accepts commands such as `ls`, `pwd`, `whoami`, `uname`, `cat flag.txt`, `help`, `exit`
- Everything is logged and visible on dashboard. No real commands are run. Safe for lab/education.

---

## Quick Start (Raspberry Pi Pico W)
- Flash with MicroPython.
- Upload `main.py`, `fake_ssh_server.py`, `fake_telnet_server.py`, `fake_ftp_server.py`, and `web_dashboard.py` via Thonny.
- Edit WiFi credentials in `main.py`.
- Run. Visit Pico's IP in browser for logs.

---

## Safety Notes
- No real vulnerabilities. Banner and shell are always fake.
- Use only in controlled/internal networks—never expose to the public/Internet.

---

## License
MIT
