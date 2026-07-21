import usocket as socket

async def start_fake_telnet():
    addr = socket.getaddrinfo("0.0.0.0", 23)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print("[*] Telnet honeypot listening on port 23")

    while True:
        conn, client = s.accept()
        print(f"[!] Fake Telnet attempt detected from {client}")
        conn.send(b"Welcome to Telnet!\n")
        conn.close()