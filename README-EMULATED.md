# PC-Compatible Emulation Version of Raspberry Pi Pico W IoT Honeypot

## Features
This is an emulation version of the Raspberry Pi Pico W Honeypot project, adapted for PC use. It uses Python `asyncio` to handle fake servers (FTP, Telnet, SSH) and the Flask framework for the web-based dashboard. 

### Supported Features:
- Fake SSH server on `127.0.0.1:2222`
- Fake Telnet server on `127.0.0.1:2323`
- Fake FTP server on `127.0.0.1:2121`
- Flask web dashboard to display attacker connection logs (`http://127.0.0.1:5000`)

## Prerequisites
1. Install Python 3.8+
2. Install dependencies: 
   ```bash
   pip install flask
   ```
3. Ensure firewall or antivirus does **not** block connections on localhost test ports.

## Usage
1. Clone this directory.
2. Run `pc_emulated_honeypot.py` with:
   ```bash
   python pc_emulated_honeypot.py
   ```
3. Start performing fake attacks by trying to `telnet`, `ssh`, or `ftp` into localhost on the respective ports.
4. Visit the dashboard in your browser to view connection logs at:
   ```
   http://127.0.0.1:5000
   ```

## Example Logs
### Serial / Console:
```
[*] SSH honeypot listening on 127.0.0.1:2222
[+] Logged: SSH attempt from 127.0.0.1
[*] Telnet honeypot listening on 127.0.0.1:2323
[+] Logged: Telnet attempt from 127.0.0.1
[*] FTP honeypot listening on 127.0.0.1:2121
[+] Logged: FTP attempt from 127.0.0.1
```

### Dashboard Output (Browser):
| Time                | Service | IP           |
|---------------------|---------|--------------|
| 2026-07-18 10:10:10 | SSH     | 127.0.0.1    |
| 2026-07-18 10:11:12 | Telnet  | 127.0.0.1    |

## Notes
- This is for testing only on a local machine. It does not simulate a real device or networking stack.
- Best for safely testing how the logging and dashboard integration works.

---
**Enjoy testing your IoT honeypot concepts!**