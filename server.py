import socket
import threading
from pathlib import Path

HOST = "0.0.0.0"
PORT = 5001
STORAGE_DIR = Path("server_storage")
MAX_LINE = 8192


def recv_line(conn: socket.socket) -> str:
    buffer = bytearray()
    while True:
        chunk = conn.recv(1)
        if not chunk:
            raise ConnectionError("Connection closed")
        buffer.extend(chunk)
        if len(buffer) > MAX_LINE:
            raise ValueError("Line too long")
        if chunk == b"\n":
            return buffer.decode("utf-8", errors="replace").rstrip("\n")


def send_line(conn: socket.socket, text: str) -> None:
    conn.sendall((text + "\n").encode("utf-8"))


def handle_client(conn, addr):
    print(f"[+] Client connected: {addr}")
    try:
        while True:
            try:
                line = recv_line(conn).strip()
            except ConnectionError:
                break

            if not line:
                send_line(conn, "ERR Empty command")
                continue

            send_line(conn, f"OK {line}")

    except Exception as e:
        print(f"[!] Client error {addr}: {e}")
    finally:
        conn.close()
        print(f"[-] Client disconnected: {addr}")


def main():
    STORAGE_DIR.mkdir(exist_ok=True)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen()

        print(f"Server started on {HOST}:{PORT}")
        print(f"Storage dir: {STORAGE_DIR.resolve()}")

        while True:
            try:
                conn, addr = server.accept()
                thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
                thread.start()
            except KeyboardInterrupt:
                print("\nServer stopped")
                break
            except Exception as e:
                print(f"[!] Accept error: {e}")


if __name__ == "__main__":
    main()