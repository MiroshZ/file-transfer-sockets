import socket
import threading
from pathlib import Path

HOST = "0.0.0.0"
PORT = 5001
STORAGE_DIR = Path("server_storage")


def handle_client(conn, addr):
    print(f"[+] Client connected: {addr}")
    try:
        conn.sendall(b"Connected to server\n")
    except Exception:
        pass
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