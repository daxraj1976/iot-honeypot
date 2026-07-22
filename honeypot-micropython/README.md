# MicroPython (Pico W) Honeypot Quickstart

This folder contains a version of the honeypot for Raspberry Pi Pico W running MicroPython. It provides simple fake servers for SSH, Telnet, and FTP, logging to memory, and a dashboard viewable in your web browser.

---

## 📦 Files

- `main.py` (entry point)
- `fake_ssh_server.py` (SSH emulation)
- `fake_telnet_server.py` (Telnet emulation)
- `fake_ftp_server.py` (FTP emulation)
- `web_dashboard.py` (mini web dashboard for logs)

---

## ⚡ Quick Guide (Thonny + Pico W)

1. **Flash MicroPython firmware** ([Get it here](https://micropython.org/download/rp2-pico-w/)), hold BOOTSEL, drag `.uf2` in.
2. **Open Thonny** and select MicroPython (Raspberry Pi Pico) as the interpreter.
3. **Install `microdot` on Pico** (for dashboard):
   ```python
   import mip
   mip.install('microdot')
   ```
4. **Upload all .py files** to Pico using Thonny (`File -> Save as` → Raspberry Pi Pico).
5. **Edit your WiFi in `main.py`**:
   ```python
   WIFI_SSID = "YOUR_WIFI"
   WIFI_PASSWORD = "YOUR_PASS"
   ```
6. **Run `main.py`** (hit Run in Thonny). Wait for IP printout. View logs at `http://<pico-ip>/` from another device!
7. **Test:**
   ```bash
   telnet <pico-ip> 23
   nc <pico-ip> 22
   ftp <pico-ip> 21
   ```
8. **View logs on the dashboard** in your browser (web_dashboard.py runs at `/`).

---

## 🛑 Limitations
- Logs vanish after reboot (RAM only, no file system used).
- Banners only. No command interactivity.
- Tested on Pico W with latest MicroPython firmware.

---

## 🛠️ Customize
- To change banners, edit the `conn.send(...)` lines in each server file.
- Dashboard code is plain HTML—change columns or look as needed.

---

## 🤝 Credit
- Based on ideas and starter code by Hermes AI agent and user (2026).
