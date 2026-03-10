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


def recv_exact(conn: socket.socket, size: int) -> bytes:
    data = bytearray()
    while len(data) < size:
        chunk = conn.recv(size - len(data))
        if not chunk:
            raise ConnectionError("Connection closed during file transfer")
        data.extend(chunk)
    return bytes(data)


def safe_filename(name: str) -> str:
    return Path(name).name


def handle_client(conn, addr):
    print(f"[+] Client connected: {addr}")
    try:
        while True:
            try:
                line = recv_line(conn).strip()
            except ConnectionError:
                print(f"[-] Connection lost: {addr}")
                break
            except Exception as e:
                print(f"[!] Read error from {addr}: {e}")
                break

            if not line:
                send_line(conn, "ERR Empty command")
                continue

            parts = line.split()
            command = parts[0].upper()

            if command == "LIST":
                try:
                    files = []
                    for file_path in STORAGE_DIR.iterdir():
                        if file_path.is_file():
                            files.append((file_path.name, file_path.stat().st_size))

                    send_line(conn, f"OK {len(files)}")
                    for name, size in sorted(files):
                        send_line(conn, f"{name} {size}")
                except Exception as e:
                    send_line(conn, f"ERR LIST_FAILED {e}")

            elif command == "UPLOAD":
                if len(parts) != 3:
                    send_line(conn, "ERR Usage: UPLOAD <filename> <size>")
                    continue

                filename = safe_filename(parts[1])

                try:
                    size = int(parts[2])
                except ValueError:
                    send_line(conn, "ERR Invalid file size")
                    continue

                if size <= 0:
                    send_line(conn, "ERR EMPTY_FILE")
                    continue

                target_path = STORAGE_DIR / filename

                try:
                    file_data = recv_exact(conn, size)
                    with open(target_path, "wb") as file:
                        file.write(file_data)
                    send_line(conn, "OK")
                    print(f"[=] Uploaded: {filename} ({size} bytes) from {addr}")
                except ConnectionError:
                    print(f"[-] Upload interrupted: {addr}")
                    break
                except Exception as e:
                    send_line(conn, f"ERR UPLOAD_FAILED {e}")

            elif command == "DOWNLOAD":
                if len(parts) != 2:
                    send_line(conn, "ERR Usage: DOWNLOAD <filename>")
                    continue

                filename = safe_filename(parts[1])
                target_path = STORAGE_DIR / filename

                if not target_path.exists() or not target_path.is_file():
                    send_line(conn, "ERR NOT_FOUND")
                    continue

                try:
                    file_size = target_path.stat().st_size
                    if file_size <= 0:
                        send_line(conn, "ERR EMPTY_FILE")
                        continue

                    send_line(conn, f"OK {file_size}")

                    with open(target_path, "rb") as file:
                        while True:
                            chunk = file.read(4096)
                            if not chunk:
                                break
                            conn.sendall(chunk)
                except ConnectionError:
                    print(f"[-] Download interrupted: {addr}")
                    break
                except Exception as e:
                    send_line(conn, f"ERR DOWNLOAD_FAILED {e}")

            elif command == "EXIT":
                send_line(conn, "OK BYE")
                break

            else:
                send_line(conn, "ERR UNKNOWN_COMMAND")

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