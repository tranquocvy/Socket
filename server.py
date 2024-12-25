import socket
import os 
import threading
import time
import datetime
import shutil
import signal
import sys
from tkinter import *
from tkinter import messagebox
import atexit
#Cấu hình server
HOST = "127.0.0.1"
PORT = 65432
STORAGE_DIR = "D:/Socket/Storage"
LOG_DIR = "D:/Socket/logs"
PIN_PATH="D:/Socket/PIN.txt"

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok = True)

def handle_client(client_socket, address, logs):
    formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
    logs.write(f"{formatted_datetime} [{address}] Client connected: {address}\n")
    print(f"Client connected: {address}")
    try:
        while True:
            # # Nhận mã pin
            # pin = client_socket.recv(1024).decode('utf-8')
            # with open(PIN_PATH,'r') as readPin:
            #     client_pin = readPin.read()
            # if pin == client_pin:
            #     client_socket.send(f"READY".encode('utf-8'))
            # else:
            #     client_socket.send(f"NO".encode('utf-8'))

            # Nhận lệnh từ client
            command = client_socket.recv(1024).decode()
            if not command:
                break
            print(f"Received command: {command} from {address}")
            formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
            logs.write(f"{formatted_datetime} [{address}] Received command: {command} from {address}\n")

            if command.startswith("upload"):
                client_socket.send(b'ACK')
                _, filename = command.split(" ", 1)
                filepath = os.path.join(STORAGE_DIR, filename)
                basename, extension = os.path.splitext(filepath)
                #Làm file với timestamp
                formatted_datetime = datetime.datetime.now().strftime("%H.%M.%S_%d.%m.%Y")
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
                formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
                logs.write(f"{formatted_datetime} [{address}] File {filename} saved as {new_filepath}\n")
                client_socket.send(f"Upload {filename} success".encode('utf-8'))

            elif command.startswith("folder_upload"):
                client_socket.send(b"ACK")

                _, folder_name = command.split(" ", 1)
                folderpath = os.path.join(STORAGE_DIR, folder_name)
                basename, extension = os.path.splitext(folderpath)
                formatted_datetime = datetime.datetime.now().strftime("%H.%M.%S_%d.%m.%Y")
                new_folderpath = f"{basename}_{formatted_datetime}{extension}"

                os.makedirs(new_folderpath, exist_ok=True)  # Tạo folder gốc trên server
                
                while True:
                    data = client_socket.recv(1024).decode('utf-8')
                    client_socket.send(b"ACK")
                    if data == "FOLDER_END":
                        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
                        logs.write(f"{formatted_datetime} [{address}] Folder {folder_name} upload completed")
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

                        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
                        print(f"File {relative_path} saved to {file_path}")
                        logs.write(f"{formatted_datetime} [{address}] File {relative_path} saved to {file_path}\n")

            elif command.startswith("download"):
                _, filename = command.split(" ", 1)
                filepath = os.path.join(STORAGE_DIR, filename)
                if os.path.isfile(filepath):
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath)
                        client_socket.send(f"READY {file_size}".encode())
                        with open(filepath, 'rb') as f:
                            while (data := f.read(1024)):
                                client_socket.send(data)
                                client_socket.recv(1024)
                        client_socket.send(b"END")
                        print(f"File {filename} sent to {address}")
                        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
                        logs.write(f"{formatted_datetime} [{address}] File {filename} sent to {address}\n")
                    else:
                        client_socket.send(f"Error: {filename} not found".encode())
                elif os.path.isdir(filepath):
                    zip_filename = f"{filepath}.zip"
                    zip_filepath = os.path.join(STORAGE_DIR, zip_filename)
                    shutil.make_archive(zip_filepath.replace(".zip", ""), 'zip', filepath)
                    if os.path.exists(zip_filepath):
                        file_size = os.path.getsize(zip_filepath)
                        client_socket.send(f"READY {file_size}".encode())
                        with open(zip_filepath, 'rb') as f:
                            while (data := f.read(1024)):
                                client_socket.send(data)
                                client_socket.recv(1024)
                        client_socket.send(b"END")
                        print(f"File {zip_filename} sent to {address}")
                        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
                        logs.write(f"{formatted_datetime} [{address}] File {filename} sent as {zip_filename} to {address}\n")
                        os.remove(zip_filepath)
                    else:
                        client_socket.send(f"Error: {filename} not found".encode())

    except Exception as e:
        print(f"Error handling client {address}: {e}")
        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
        logs.write(f"{formatted_datetime} [{address}] Client disconnected unexpectedly.\n")
    finally:
        print(f"Client disconnected: {address}")
        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
        logs.write(f"{formatted_datetime} [{address}] Client disconnected: {address}\n")
        client_socket.close()

def cleanup():
    global server, logs
    if server:
        server.close()
        print("Server closed.")
    if logs:
        logs.close()
        print("Log file closed.")

# def main():
#     server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     server.bind((HOST, PORT))
#     server.listen(5)

#     formatted_datetime = datetime.datetime.now().strftime("%H.%M.%S_%d.%m.%Y")
#     filelogs=f"{LOG_DIR}/{formatted_datetime}.txt"

#     with open(filelogs,'w') as logs:
#         formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
#         logs.write(f"{formatted_datetime} [Server] Server running on {HOST}:{PORT}\n")
#         print(f"Server running on {HOST}:{PORT}")
#         try:
#             while True:
#                 client_socket, address = server.accept()
#                 threading.Thread(target=handle_client, args=(client_socket, address, logs)).start()   
#         except KeyboardInterrupt:
#             logs.close()
#             server.close()
#         finally:
#             server.close()
#             logs.close()
#             print("Server close")
# if __name__ == "__main__":
#     main()

def main():
    global server, logs
    atexit.register(cleanup)

    # Tạo socket server
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    formatted_datetime = datetime.datetime.now().strftime("%H.%M.%S_%d.%m.%Y")
    filelogs = f"{LOG_DIR}/{formatted_datetime}.txt"

    logs = open(filelogs, 'w')
    formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
    logs.write(f"{formatted_datetime} [Server] Server running on {HOST}:{PORT}\n")
    print(f"Server running on {HOST}:{PORT}")

    try:
        while True:
            client_socket, address = server.accept()
            threading.Thread(target=handle_client, args=(client_socket, address, logs)).start()
    except KeyboardInterrupt:
        print("KeyboardInterrupt detected. Cleaning up resources...")

if __name__ == "__main__":
    main()