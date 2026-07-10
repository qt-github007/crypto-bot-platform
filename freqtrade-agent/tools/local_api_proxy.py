import select
import socket
import socketserver
import sys


class ProxyHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        upstream = socket.create_connection((TARGET_HOST, TARGET_PORT), timeout=10)
        sockets = [self.request, upstream]

        try:
            while True:
                readable, _, _ = select.select(sockets, [], [], 60)
                for sock in readable:
                    data = sock.recv(65536)
                    if not data:
                        return
                    peer = upstream if sock is self.request else self.request
                    peer.sendall(data)
        finally:
            upstream.close()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: local_api_proxy.py <listen_port> <target_host> <target_port>")

    LISTEN_PORT = int(sys.argv[1])
    TARGET_HOST = sys.argv[2]
    TARGET_PORT = int(sys.argv[3])

    with socketserver.ThreadingTCPServer(("0.0.0.0", LISTEN_PORT), ProxyHandler) as server:
        server.daemon_threads = True
        server.serve_forever()

