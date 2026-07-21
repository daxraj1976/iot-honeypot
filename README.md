# Smart IoT Honeypot Using Raspberry Pi Pico W

## Project Overview
This is a low-cost IoT honeypot designed for threat analysis. It runs on a Raspberry Pi Pico W and emulates common network services. The honeypot safely logs unsolicited connection attempts and records attacker activity without providing actual access to services.

### Features:
- **Fake Servers** for SSH, Telnet, and FTP
- **Logger** to track connection attempts (IP, service, time)
- **Web Dashboard** to visualize attack data

---

## System Requirements

### Hardware:
- Raspberry Pi Pico W
- Micro USB Cable

### Software:
- MicroPython or CircuitPython installed on the Pico
- `Thonny` IDE on your computer

#### Libraries:
- `usocket`, `uasyncio`, `microdot` (install via Thonny if not preinstalled)
- Networking functionality (preloaded into MicroPython)

---

## File Structure

```
honeypot/
├── main.py
├── fake_ssh_server.py
├── fake_telnet_server.py
├── fake_ftp_server.py
├── web_dashboard.py
└── README.md
```

---

## How It Works
### 1. **Fake Services**:
   - Fake SSH Server on port 22
   - Fake Telnet Server on port 23
   - Fake FTP Server on port 21
   - Logs connection attempts.

### 2. **Logger**:
   - Records each connection with the IP, service, and time.
   
### 3. **Dashboard**:
   - Accessible on Pico's default IP (port 80).
   - Displays connection details in an easy-to-read table.

---

## Step-by-Step Setup

### 1. Flash MicroPython to Pico W:
   - Download MicroPython: [Micropython Pico W Firmware](https://micropython.org/)
   - Flash using the official guide.

### 2. Transfer Files:
   - Upload all `.py` files to the Pico using `Thonny` IDE.

### 3. Run the Honeypot:
   - Use `Thonny` and execute `main.py`.

### 4. Access the Dashboard:
   - Open a browser and visit:
     ```
     http://<Pico-IP>/
     ```
   - Example: `192.168.4.1`

---

## Example Logs
### Serial Output:
```
[*] SSH honeypot listening on port 22
[!] Fake SSH attempt detected from 192.168.0.56
[+] Logged: SSH attempt from 192.168.0.56

[*] Telnet honeypot listening on port 23
[!] Fake Telnet attempt detected from 192.168.0.56
[+] Logged: Telnet attempt from 192.168.0.56
```

### Dashboard View:
| Time                | Service | IP           |
|---------------------|---------|--------------|
| 2026-07-18 10:10:10 | SSH     | 192.168.0.56 |
| 2026-07-18 10:11:12 | Telnet  | 192.168.0.56 |

---

## Troubleshooting
- **No Logs**: Check if your Pico is connected to the desired Wi-Fi Network.
- **Dashboard Error**: Ensure `web_dashboard.py` is running.
- **Unknown Issues**: Reset the Pico and reflash MicroPython.

---

## Future Enhancements
- Add malware emulation detection with dummy files.
- Extend to support additional protocols (e.g., HTTP).
- Enable cloud logging/dashboard.

---

**Enjoy your IoT Honeypot!**