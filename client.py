import socket

def main():
    host = input("Server IP: ").strip() or "127.0.0.1"
    port = int(input("Server port: ").strip() or "5001")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((host, port))
        data = client.recv(1024)
        print(data.decode("utf-8", errors="replace"))


if __name__ == "__main__":
    main()