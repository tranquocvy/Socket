import socket
import os
import threading
import datetime
import shutil
import time
from tkinter import *
from tkinter import messagebox

# Cấu hình server
HOST = "127.0.0.1"
PORT = 65432
STORAGE_DIR = "D:/Socket/Storage"
LOG_DIR = "D:/Socket/logs"
PIN_PATH = "D:/Socket/PIN.txt"

os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Biến toàn cục
server_socket = None
server_thread = None
is_running = False

def handle_client(client_socket, address, logs):
    formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
    logs.write(f"{formatted_datetime} [{address}] Client connected: {address}\n")
    print(f"Client connected: {address}")

    # Nhận mã pin
    pin = client_socket.recv(1024).decode('utf-8')
    with open(PIN_PATH,'r') as readPin:
        client_pin = readPin.read()
    if pin == client_pin:
        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
        logs.write(f"{formatted_datetime} [{address}] PIN correct\n")
        print("PIN correct")
        client_socket.send(f"READY".encode('utf-8'))
    else:
        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
        logs.write(f"{formatted_datetime} [{address}] PIN wrong\n")
        print("PIN wrong")
        client_socket.send(f"NO".encode('utf-8'))

    try:
        while True:
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
                        logs.write(f"{formatted_datetime} [{address}] Folder {folder_name} upload completed\n")
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
                        logs.write(f"{formatted_datetime} [Server] File {filename} sent to {address}\n")
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
                        print(f"Folder {filename} sent as {zip_filename} to {address}")
                        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
                        logs.write(f"{formatted_datetime} [Server] Folder {filename} sent as {zip_filename} to {address}\n")
                        os.remove(zip_filepath)
                    else:
                        client_socket.send(f"Error: {filename} not found".encode())

    except Exception as e:
        print(f"Error handling client {address}: {e}")
        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
        logs.write(f"{formatted_datetime} [{address}] Error handling client {address}: {e}\n")
    finally:
        print(f"Client disconnected: {address}")
        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
        logs.write(f"{formatted_datetime} [{address}] Client disconnected: {address}\n")
        client_socket.close()


def accept_clients():
    """Hàm chấp nhận client, chạy trên một thread riêng."""
    global is_running
    formatted_datetime = datetime.datetime.now().strftime("%H.%M.%S_%d.%m.%Y")
    filelogs = f"{LOG_DIR}/{formatted_datetime}.txt"
    with open(filelogs, 'w') as logs:
        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
        logs.write(f"{formatted_datetime} [Server] Server running on {HOST}:{PORT}\n")
        print(f"Server running on {HOST}:{PORT}")
        try:
            while is_running:
                client_socket, address = server_socket.accept()
                threading.Thread(target=handle_client, args=(client_socket, address, logs)).start()
        except Exception as e:
            if is_running:
                formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
                logs.write(f"{formatted_datetime} [Server] Error accepting client: {e}\n")
                print(f"Error accepting client: {e}")
        finally:
            formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
            logs.write(f"{formatted_datetime} [Server] Server stopped\n")
            logs.close()
            print("Server stopped")

def start_server(start_button, end_button):
    """Hàm khởi động server."""
    global server_socket, server_thread, is_running

    if is_running:
        messagebox.showinfo("Info", "Server is already running!")
        return

    try:
        # Tạo socket
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, PORT))
        server_socket.listen(100)
        is_running = True

        # Chạy thread chấp nhận client
        server_thread = threading.Thread(target=accept_clients)
        server_thread.daemon = True
        server_thread.start()

        # Cập nhật GUI
        start_button.config(state="disabled")
        end_button.config(state="normal")
        messagebox.showinfo("Server", "Server started successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to start server: {e}")


def end_server(start_button, end_button):
    """Hàm dừng server."""
    global server_socket, is_running

    if not is_running:
        messagebox.showinfo("Info", "Server is not running!")
        return

    try:
        is_running = False
        server_socket.close()

        # Cập nhật GUI
        start_button.config(state="normal")
        end_button.config(state="disabled")
        messagebox.showinfo("Server", "Server stopped successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to stop server: {e}")

def on_close(root):
    global is_running
    if is_running:
        is_running = False
        server_socket.close()  # Đóng socket server
        # Đảm bảo thread chấp nhận client sẽ thoát
        server_thread.join()  # Chờ thread hoàn thành trước khi tắt
        time.sleep(1)
    root.quit()  # Đóng cửa sổ GUI

def main():
    # Tạo GUI
    root = Tk()
    root.title("TCP/IP Server Control")
    root.geometry("300x150")

    # Nút Start Server
    start_button = Button(root, text="Start Server", font=("Arial", 14), command=lambda:start_server(start_button, end_button))
    start_button.pack(pady=20)

    # Nút End Server
    end_button = Button(root, text="End Server", font=("Arial", 14), command=lambda:end_server(start_button, end_button), state="disabled")
    end_button.pack(pady=10)

    # Xử lý khi người dùng đóng cửa sổ
    root.protocol("WM_DELETE_WINDOW", lambda:on_close(root))

    # Chạy GUI
    root.mainloop()

if __name__ == "__main__":
    main()