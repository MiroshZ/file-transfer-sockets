import socket
from pathlib import Path

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


def main():
    host = input("Server IP: ").strip() or "127.0.0.1"
    port = int(input("Server port: ").strip() or "5001")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((host, port))
        print("Connected to server")

        while True:
            cmd = input("> ").strip()
            if not cmd:
                continue

            parts = cmd.split()
            operation = parts[0].upper()

            try:
                if operation == "LIST":
                    send_line(client, cmd)
                    response = recv_line(client)

                    header = response.split()
                    if len(header) == 2 and header[0] == "OK":
                        count = int(header[1])
                        if count == 0:
                            print("(empty)")
                        else:
                            for _ in range(count):
                                print(recv_line(client))
                    else:
                        print("Server:", response)

                elif operation == "UPLOAD":
                    if len(parts) != 2:
                        print("Usage: UPLOAD <path_to_file>")
                        continue

                    path = Path(parts[1])
                    if not path.exists() or not path.is_file():
                        print("Error: file not found")
                        continue

                    size = path.stat().st_size
                    if size <= 0:
                        print("Error: empty file")
                        continue

                    send_line(client, f"UPLOAD {path.name} {size}")

                    with open(path, "rb") as file:
                        while True:
                            chunk = file.read(4096)
                            if not chunk:
                                break
                            client.sendall(chunk)

                    print("Server:", recv_line(client))

                else:
                    send_line(client, cmd)
                    print("Server:", recv_line(client))

                if operation == "EXIT":
                    break

            except ConnectionError:
                print("Connection lost")
                break
            except Exception as e:
                print("Error:", e)


if __name__ == "__main__":
    main()