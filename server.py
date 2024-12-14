import os
import socket
import threading
from datetime import datetime

# Cấu hình server
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65432
BUFFER_SIZE = 4096
UPLOAD_DIR = 'server_files'
FORMAT = "utf8"
# Đảm bảo thư mục lưu trữ file tồn tại
os.makedirs(UPLOAD_DIR, exist_ok=True)

def handle_client(client_socket, client_address):
    print(f"[{datetime.now()}] Kết nối từ {client_address}")

    while True:
        try:
            # Nhận lệnh từ client
            command = client_socket.recv(BUFFER_SIZE).decode()
            if not command:
                break
            
            cmd, *args = command.split()

            if cmd == "upload":
                filename = args[0]
                filepath = os.path.join(UPLOAD_DIR, filename)
                
                # Đảm bảo tên file duy nhất
                base, ext = os.path.splitext(filepath)
                counter = 1
                while os.path.exists(filepath):
                    filepath = f"{base}_{counter}{ext}"
                    counter += 1

                # Nhận dữ liệu file từ client
                with open(filepath, 'wb') as f:
                    while True:
                        data = client_socket.recv(BUFFER_SIZE)
                        if data == b"EOF":
                            break
                        f.write(data)
                client_socket.send("Upload thành công.")

            elif cmd == "download":
                filename = args[0]
                filepath = os.path.join(UPLOAD_DIR, filename)

                if os.path.exists(filepath):
                    with open(filepath, 'rb') as f:
                        while chunk := f.read(BUFFER_SIZE):
                            client_socket.send(chunk)
                    client_socket.send(b"EOF")
                else:
                    client_socket.send("File không tồn tại.")

            else:
                client_socket.send("Lệnh không hợp lệ.")

        except (ConnectionResetError, BrokenPipeError):
            print(f"[{datetime.now()}] Mất kết nối từ {client_address}")
            break

    client_socket.close()

def start_server():
    # Tạo socket server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)
    print(f"Server lắng nghe tại {SERVER_HOST}:{SERVER_PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        thread.start()
        print(f"[{datetime.now()}] Đang xử lý {threading.active_count() - 1} client")

if __name__ == "__main__":
    start_server()
