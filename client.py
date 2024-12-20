import socket
import os
import time

# Cấu hình client
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432

def upload_file(client_socket, filepath):
    if not os.path.exists(filepath):
        print(f"Error: Path {filepath} not found")  
        return

    filename = os.path.basename(filepath)
    if os.path.isfile(filepath):
        client_socket.send(f"upload {filename}".encode('utf-8'))
        client_socket.recv(1024)
        #Tính toán kích thước file
        total_size = os.path.getsize(filepath)
        byte_sent = 0
        #Upload
        with open(filepath, 'rb') as f:
            while (data := f.read(1024)):
                client_socket.send(data)
                client_socket.recv(1024)
                #Cập nhật byte đã gửi
                byte_sent += len(data)
                #Tính toán phần trăm và hiển thị tiến độ
                progress = (byte_sent/total_size)*100
                print(f"\rUploading: {progress:.2f}% completed", end="")
        client_socket.send(b'END')
        print("\nUpload completed!")
        print(client_socket.recv(1024).decode('utf-8'))
        
    elif os.path.isdir(filepath):
        client_socket.send(f"folder_upload {filename}".encode('utf-8'))
        ack = client_socket.recv(1024)

        for root, dirs, files in os.walk(filepath):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, filepath)

                # Gửi thông tin file
                client_socket.send(f"file {relative_path}".encode('utf-8'))
                ack = client_socket.recv(1024)
                #Tính toán kích thước file
                total_size = os.path.getsize(file_path)
                byte_sent = 0
                # Gửi nội dung file
                with open(file_path, 'rb') as f:
                    while (data := f.read(1024)):
                        client_socket.send(data)
                        ack = client_socket.recv(1024)
                        #Cập nhật byte đã gửi
                        byte_sent += len(data)
                        #Tính toán phần trăm và hiển thị tiến độ
                        progress = (byte_sent/total_size)*100
                        print(f"\rUploading: {progress:.2f}% completed", end="")
                client_socket.send(b'END')
                ack=client_socket.recv(1024)
                print("\nUpload completed!")

        client_socket.send(b'FOLDER_END')
        client_socket.recv(1024)
        print(client_socket.recv(1024).decode('utf-8'))

def download_file(client_socket, filename):
    client_socket.send(f"download {filename}".encode())
    response = client_socket.recv(1024).decode()
   
    if response.startswith("READY"):
        #Lấy kích thước file do bên server gửi về 
        _, file_size = response.split(" ")
        file_size = int(file_size)
        download_path = input("Nhap duong dan:  ")
        if not os.path.isdir(download_path):
            os.makedirs(download_path)
        filename = os.path.basename(filename)
        file_path = os.path.join(download_path, filename)

        byte_received = 0
        with open(file_path, 'wb') as f:
            while True:
                data = client_socket.recv(1024)
                if data == b"END":
                    break
                else:
                    f.write(data)
                    client_socket.send(b"ACK")
                    byte_received += len(data)
                    progress = (byte_received/file_size)*100
                    print(f"\rDownloading {filename}: {progress:.2f}% completed", end="")

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