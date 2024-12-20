import socket
import os 
import threading
import time
import datetime
#Cấu hình server
HOST = "127.0.0.1"
PORT = 65432
STORAGE_DIR = "D:/Socket/Storage"

os.makedirs(STORAGE_DIR, exist_ok=True)

def handle_client(client_socket, address):
    print(f"Client connected: {address}")
    try:
        while True:
            # Nhận lệnh từ client
            command = client_socket.recv(1024).decode()
            if not command:
                break
            print(f"Received command: {command} from {address}")

            if command.startswith("upload"):
                client_socket.send(b'ACK')
                _, filename = command.split(" ", 1)
                filepath = os.path.join(STORAGE_DIR, filename)
                basename, extension = os.path.splitext(filepath)
                current_datetime = datetime.datetime.now()
                formatted_datetime = current_datetime.strftime("%H.%M.%S_%d.%m.%Y")
                new_filepath = f"{basename}_{formatted_datetime}{extension}"

                with open(new_filepath, 'wb') as f:
                    while True:
                        data = client_socket.recv(1024)
                        if data == b"END":
                            break
                        else:
                            f.write(data)
                            client_socket.send(b"ACK")

                print(f"File {filename} saved as {new_filepath}")
                client_socket.send(f"Upload {filename} success".encode('utf-8'))

            elif command.startswith("folder_upload"):
                client_socket.send(b"ACK")

                _, folder_name = command.split(" ", 1)
                folderpath = os.path.join(STORAGE_DIR, folder_name)
                basename, extension = os.path.splitext(folderpath)
                current_datetime = datetime.datetime.now()
                formatted_datetime = current_datetime.strftime("%H.%M.%S_%d.%m.%Y")
                new_folderpath = f"{basename}_{formatted_datetime}{extension}"

                os.makedirs(new_folderpath, exist_ok=True)  # Tạo folder gốc trên server
                
                while True:
                    data = client_socket.recv(1024).decode('utf-8')
                    client_socket.send(b"ACK")
                    if data == "FOLDER_END":
                        print(f"Folder {folder_name} upload completed")
                        client_socket.send(f"Upload folder {folder_name} success".encode('utf-8'))
                        break

                    if data.startswith("file"):
                        _, relative_path = data.split(" ", 1)
                        file_path = os.path.join(new_folderpath, relative_path)
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Tạo lại cấu trúc thư mục

                        with open(file_path, 'wb') as f:
                            while True:
                                data = client_socket.recv(1024)
                                if data == b"END":
                                    client_socket.send(b"ACK")
                                    break
                                else:
                                    f.write(data)
                                    client_socket.send(b"ACK")

                        print(f"File {relative_path} saved to {file_path}")

            elif command.startswith("download"):
                _, filename = command.split(" ", 1)
                filepath = os.path.join(STORAGE_DIR, filename)
                if os.path.exists(filepath):
                    client_socket.send(f"READY".encode())
                    with open(filepath, 'rb') as f:
                        while (data := f.read(1024)):
                            client_socket.send(data)
                    client_socket.send(b"END")
                    print(f"File {filename} sent to {address}")
                else:
                    client_socket.send(f"Error: {filename} not found".encode())

            else:
                client_socket.send(f"Invalid command: {command}".encode())

    except Exception as e:
        print(f"Error handling client {address}: {e}")
    finally:
        print(f"Client disconnected: {address}")
        client_socket.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server running on {HOST}:{PORT}")

    while True:
        client_socket, address = server.accept()
        threading.Thread(target=handle_client, args=(client_socket, address)).start()

if __name__ == "__main__":
    main()