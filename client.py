import socket

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

            send_line(client, cmd)
            response = recv_line(client)

            if operation == "LIST":
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
            else:
                print("Server:", response)

            if operation == "EXIT":
                break


if __name__ == "__main__":
    main()