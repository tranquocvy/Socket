import socket
import os

# Cấu hình client
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432

def upload_file(client_socket, filepath):
    if not os.path.exists(filepath):
        print(f"Error: File {filepath} not found")
        return

    filename = os.path.basename(filepath)
    client_socket.send(f"upload {filename}".encode())
    with open(filepath, 'rb') as f:
        while (data := f.read(1024)):
            client_socket.send(data)
    client_socket.send(b"END")
    print(client_socket.recv(1024).decode())

def download_file(client_socket, filename):
    client_socket.send(f"download {filename}".encode())
    response = client_socket.recv(1024).decode()

    if response == "READY":
        with open(filename, 'wb') as f:
            while True:
                data = client_socket.recv(1024)
                if data == b"END":
                    break
                f.write(data)
        print(f"File {filename} downloaded successfully")
    else:
        print(response)

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    print("Connected to server")

    try:
        while True:
            command = input("Enter command (upload <file> / download <file> / exit): ")
            if command == "exit":
                break
            elif command.startswith("upload"):
                _, filepath = command.split(" ", 1)
                upload_file(client_socket, filepath)
            elif command.startswith("download"):
                _, filename = command.split(" ", 1)
                download_file(client_socket, filename)
            else:
                print("Invalid command")
                
    finally:
        client_socket.close()
        print("Disconnected from server")

if __name__ == "__main__":
    main()