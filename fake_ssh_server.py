import usocket as socket

async def start_fake_ssh():
    addr = socket.getaddrinfo("0.0.0.0", 22)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print("[*] SSH honeypot listening on port 22")

    while True:
        conn, client = s.accept()
        print(f"[!] Fake SSH attempt detected from {client}")
        conn.send(b"SSH-2.0-OpenSSH_8.2\r\n")
        conn.close()