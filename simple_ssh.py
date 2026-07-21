#!/usr/bin/env python3
"""
Simple SSH honeypot test
"""
import asyncio
from datetime import datetime

class SimpleSSHProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        ip = peername[0] if peername else 'unknown'
        print(f'SSH connection from {ip}')
        # Send SSH identification string
        transport.write(b'SSH-2.0-OpenSSH_7.9p1 Debian-10\r\n')
        # Close the connection after sending banner
        transport.close()

async def main():
    # Try a high port to avoid permission issues
    server = await asyncio.start_server(SimpleSSHProtocol, '127.0.0.1', 2222)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')
    
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Server stopped')