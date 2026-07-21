import usocket as socket

async def start_fake_ftp():
    addr = socket.getaddrinfo("0.0.0.0", 21)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)
    print("[*] FTP honeypot listening on port 21")

    while True:
        conn, client = s.accept()
        print(f"[!] Fake FTP attempt detected from {client}")
        conn.send(b"220 (vsftp 3.0.3)\n")
        conn.close()