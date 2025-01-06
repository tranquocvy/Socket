import socket
import os
import threading
import datetime
import shutil
import time
import tkinter as tk
from tkinter import *
from tkinter import scrolledtext
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
logs = None
is_running = False
active_clients = [] # Lưu trữ các client đã kết nối
client_threads = [] # Lữu trữ các thread đang hoạt động
log_area = None # Ghi logs ra GUI
client_pin = "" # Lưu pin

# Hàm ghi logs vào log_area
def write_log(message):
    log_area.configure(state='normal')  # Cho phép chỉnh sửa
    log_area.insert('end', f"{message}\n")  # Thêm nội dung mới
    log_area.configure(state='disabled')  # Khóa lại
    log_area.see('end')  # Cuộn xuống dòng cuối cùng

# Upload file
def upload_action(client_socket, address, command, logs):
    # Gửi 1 thông báo đến client: đã nhận được data, tiếp tục gửi data
    client_socket.send(b'ACK')

    #Lấy dữ liệu đường dẫn, gộp lấy tên, tách tên file và đuôi file
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
                # Gửi 1 thông báo đến client: đã nhận được data, tiếp tục gửi data
                client_socket.send(b"ACK")

    formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
    logs.write(f"{formatted_datetime} [{address}] File {filename} saved as {new_filepath}\n")
    write_log(f"{formatted_datetime} [{address}] File {filename} saved as {new_filepath}\n")
    client_socket.send(f"Upload {filename} success".encode('utf-8'))

# Upload folder
def upload_folder_action(client_socket, address, command, logs):
    # Gửi 1 thông báo đến client: đã nhận được data, tiếp tục gửi data
    client_socket.send(b"ACK")
    # Lấy file name từ command line tách lấy file name và extension file, gắn timestamp
    _, folder_name = command.split(" ", 1)
    folderpath = os.path.join(STORAGE_DIR, folder_name)
    basename, extension = os.path.splitext(folderpath)
    formatted_datetime = datetime.datetime.now().strftime("%H.%M.%S_%d.%m.%Y")
    new_folderpath = f"{basename}_{formatted_datetime}{extension}"

    os.makedirs(new_folderpath, exist_ok=True)  # Tạo folder gốc trên server
    
    while True:
        data = client_socket.recv(1024).decode('utf-8')
        # Gửi 1 thông báo đến client: đã nhận được data, tiếp tục gửi data
        client_socket.send(b"ACK")

        if data == "FOLDER_END":
            formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
            logs.write(f"{formatted_datetime} [{address}] Folder {folder_name} upload completed\n")
            write_log(f"{formatted_datetime} [{address}] Folder {folder_name} upload completed\n")

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
                        # Gửi 1 thông báo đến client: đã nhận được data, tiếp tục gửi data
                        client_socket.send(b"ACK")
                        break
                    else:
                        f.write(data)
                        # Gửi 1 thông báo đến client: đã nhận được data, tiếp tục gửi data
                        client_socket.send(b"ACK")

            formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
            logs.write(f"{formatted_datetime} [{address}] File {relative_path} saved to {file_path}\n")
            write_log(f"{formatted_datetime} [{address}] File {relative_path} saved to {file_path}\n")
            
# Download
def download_action(client_socket, address, command, logs):
    _, filename = command.split(" ", 1)
    filepath = os.path.join(STORAGE_DIR, filename)

    # Check nếu là file thì đây là download file
    if os.path.isfile(filepath):
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            client_socket.send(f"READY {file_size}".encode())
            ack = client_socket.recv(1024)

            with open(filepath, 'rb') as f:
                while (data := f.read(1024)):
                    client_socket.send(data)

                    # Nhận thông báo từ server: tiếc tục gửi data
                    ack = client_socket.recv(1024)

            client_socket.send(b"END")

            formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
            logs.write(f"{formatted_datetime} [Server] File {filename} sent to {address}\n")
            write_log(f"{formatted_datetime} [Server] File {filename} sent to {address}\n")
        else:
            formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
            logs.write(f"{formatted_datetime} [{address}] Error: {filename} not found\n")
            write_log(f"{formatted_datetime} [{address}] Error: {filename} not found\n")

            client_socket.send(f"Error: {filename} not found".encode())

    # Check nếu là đường dẫn là folder thì là download filezip
    elif os.path.isdir(filepath): 
        zip_filename = f"{filepath}.zip"
        zip_filepath = os.path.join(STORAGE_DIR, zip_filename)
        shutil.make_archive(zip_filepath.replace(".zip", ""), 'zip', filepath)

        if os.path.exists(zip_filepath):
            file_size = os.path.getsize(zip_filepath)
            client_socket.send(f"READY {file_size}".encode('utf-8'))
            client_socket.recv(1024)

            with open(zip_filepath, 'rb') as f:
                while (data := f.read(1024)):
                    client_socket.send(data)

                    # Nhận thông báo từ server: tiếc tục gửi data
                    client_socket.recv(1024)
            # Thông báo kết thúc truyền file
            client_socket.send(b"END")

            formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
            logs.write(f"{formatted_datetime} [Server] Folder {filename} sent as {zip_filename} to {address}\n")
            write_log(f"{formatted_datetime} [Server] Folder {filename} sent as {zip_filename} to {address}\n")

            # Xóa file zip bên server để dọn dẹp bộ nhớ
            os.remove(zip_filepath)
    else:
        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
        logs.write(f"{formatted_datetime} [{address}] Error: {filename} not found\n")
        write_log(f"{formatted_datetime} [{address}] Error: {filename} not found\n")

        client_socket.send(f"Error: {filename} not found".encode())
        client_socket.recv(1024)

# handle
def handle_client(client_socket, address, logs):
    global active_clients # Lưu trữ client

    # Thêm socket vào
    active_clients.append(client_socket)

    formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
    logs.write(f"{formatted_datetime} [{address}] Client connected: {address}\n")
    write_log(f"{formatted_datetime} [{address}] Client connected: {address}\n")

    # Nhận mã pin, check và gửi kết quả về cho client
    # Timeout nhập pin là 15s
    client_socket.settimeout(15)
    try:
        pin = client_socket.recv(1024).decode('utf-8')
    except socket.timeout:
        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
        logs.write(f"{formatted_datetime} [{address}] Client disconnected: {address}\n")
        write_log(f"{formatted_datetime} [{address}] Client disconnected: {address}\n")

        client_socket.shutdown(socket.SHUT_RDWR) # Dừng recv và send
        return

    with open(PIN_PATH,'r') as readPin:
        check_pin = readPin.read()
    if pin == check_pin:
        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
        logs.write(f"{formatted_datetime} [{address}] PIN correct\n")
        write_log(f"{formatted_datetime} [{address}] PIN correct\n")

        client_socket.send(f"READY".encode('utf-8'))
    else: # Client tự ngắt kết nối
        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
        logs.write(f"{formatted_datetime} [{address}] PIN wrong\n")
        write_log(f"{formatted_datetime} [{address}] PIN wrong\n")

        client_socket.send(f"NO".encode('utf-8'))
        
    # Giao tiếp với client
    try:
        while True:
            # Đặt thời gian chờ nhận dữ liệu là 120 giây
            client_socket.settimeout(120)

            try:
                # Nhận lệnh từ client
                command = client_socket.recv(1024).decode()
                if not command:
                    break
                if command:
                    client_socket.settimeout(None)
                formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
                logs.write(f"{formatted_datetime} [{address}] Received command: {command} from {address}\n")
                write_log(f"{formatted_datetime} [{address}] Received command: {command} from {address}\n")

                if command.startswith("upload"):
                    upload_action(client_socket, address, command, logs)

                elif command.startswith("folder_upload"):
                    upload_folder_action(client_socket, address, command, logs)

                elif command.startswith("download"):
                    download_action(client_socket, address, command, logs)

            except socket.timeout:
                # Nếu không nhận được command trong 120 giây
                break;

    except Exception as e: # Nếu có lỗi exception xảy thì đóng kết nối
        if is_running:
            formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
            logs.write(f"{formatted_datetime} [{address}] Error handling: {e}\n")
            write_log(f"{formatted_datetime} [{address}] Error handling: {e}\n")
    finally:
        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
        logs.write(f"{formatted_datetime} [{address}] Client disconnected: {address}\n")
        write_log(f"{formatted_datetime} [{address}] Client disconnected: {address}\n")

        if client_socket in active_clients:
            active_clients.remove(client_socket) # Xóa client ra khỏi list client
        if client_socket:
            client_socket.close()

def accept_clients(): # Accept client connect
    global is_running, logs, client_threads # Dùng biến toàn cục đã khai báo

    formatted_datetime = datetime.datetime.now().strftime("%H.%M.%S_%d.%m.%Y")
    filelogs = f"{LOG_DIR}/{formatted_datetime}.txt"

    with open(filelogs, 'w') as logs: # Ghi logs
        formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
        logs.write(f"{formatted_datetime} [Server] Server running on {HOST}:{PORT}\n")
        write_log(f"{formatted_datetime} [Server] Server running on {HOST}:{PORT}\n")
        print(f"Server running on {HOST}:{PORT}")

        try:
            while is_running:
                try:
                    client_socket, address = server_socket.accept()
                    thread = threading.Thread(target = handle_client, args=(client_socket, address, logs))
                    thread.start()
                    client_threads.append(thread) # Lưu lại thread đang chạy
                except OSError:
                    break

        except Exception as e:
            if is_running:
                formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
                logs.write(f"{formatted_datetime} [Server] Error accepting client: {e}\n")
                write_log(f"{formatted_datetime} [Server] Error accepting client: {e}\n")

        finally:
            formatted_datetime = datetime.datetime.now().strftime("[%H.%M.%S]")
            logs.write(f"{formatted_datetime} [Server] Server stopped\n")
            if log_area:
                write_log(f"{formatted_datetime} [Server] Server stopped\n")

def start_server(start_button, end_button):
    global server_socket, server_thread, is_running # Dùng biến toàn cục đã khai báo

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
        server_thread = threading.Thread(target = accept_clients)
        server_thread.daemon = True # Đặt trạng thái daemon cho socket -> luồng nền
        server_thread.start()       # Bắt đầu thread

        # Cập nhật nút của GUI
        start_button.config(state="disabled")
        end_button.config(state="normal")
        messagebox.showinfo("Server", "Server started successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to start server: {e}")


def end_server(start_button, end_button):
    global server_socket, is_running # Dùng biến toàn cục đã khai báo
    global active_clients, logs, client_threads
 
    if not is_running:
        messagebox.showinfo("Info", "Server is not running!")
        return

    try:
        is_running = False

        # Đóng tất cả kết nối client
        for client in active_clients:
            if client:
                client.shutdown(socket.SHUT_RDWR)  # Dừng truyền và nhận
        active_clients.clear()  # Xóa danh sách client

        for thread in client_threads:
            thread.join() # Đợi cho các thread thực hiện hết
        client_threads.clear()

        if server_socket:
            server_socket.close()

        # Chờ các luồng xử lý
        time.sleep(1)

        # Đóng file logs 
        if logs:
            logs.close()
            logs = None

        # Cập nhật nút của GUI
        start_button.config(state="normal")
        end_button.config(state="disabled")
        messagebox.showinfo("Server", "Server stopped successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to stop server: {e}")

def on_close(root):
    global is_running, log_area # Dùng biến toàn cục đã khai báo
    if log_area:
        log_area.destroy()
        log_area = None
    if is_running:
        is_running = False

        # Đóng tất cả kết nối client
        for client_socket in active_clients:
            if client_socket:
                client_socket.close()
        active_clients.clear()  # Xóa danh sách client

        server_socket.close()  # Đóng socket server

        # Đảm bảo thread chấp nhận client sẽ thoát
        server_thread.join()  # Chờ thread hoàn thành trước khi tắt, đảm bảo tài nguyên không bị rò rỉ
        time.sleep(1)

    root.quit()  # Đóng cửa sổ GUI

# Hàm xử lý mã pin
def on_key_input(event, pin_entry):
    global client_pin
    char = event.char

    # Kiểm tra nếu phím Backspace, Delete
    if event.keysym in ("BackSpace", "Delete"):
        if len(client_pin) > 0:
            client_pin = client_pin[:-1]
            pin_entry.delete(0, END)
            pin_entry.insert(0, "*" * len(client_pin))
        return "break"  # Ngăn không cho ký tự gốc xuất hiện
    
    # Kiểm tra nếu phím nhấn không hợp lệ, isprintable: false nếu kí tự không thể in ra
    if not char.isprintable() or event.keysym in ("BackSpace", "Delete", "space"):
        return
    
    # Cập nhật nội dung thực tế
    client_pin += char
    pin_entry.delete(0, END)
    pin_entry.insert(0, "*" * len(client_pin))

    # Ngăn không cho ký tự gốc xuất hiện
    return "break"

# Hàm xác nhận PIN
def verifyPin(pin_root, root):
    if(client_pin == "1234"):
        pin_root.destroy()
        root.deiconify()
    else:
        messagebox.showerror("Lỗi", "PIN wrong!")
        root.quit()

# Giao diện pin
def checkPIN(root):
    # Tạo cửa sổ chính
    pin_root = Toplevel(root)
    pin_root.title('TCP/IP')
    pin_root.minsize(height = 250, width = 500)
    pin_root.configure(bg='black')  # Màu nền của cửa sổ chính là đen

    # Hiển thị tiêu đề "Pin"
    Label(pin_root, text = 'PIN', fg = 'white', bg = 'black', font = ('Cambria', 24), 
            width = 20).grid(row = 0, column = 0, columnspan = 3, pady = 20, sticky = 'n')

    pin_entry = Entry(pin_root, width = 40, font = ('Cambria', 12), bg = 'gray', fg = 'white')
    pin_entry.grid(row = 2, column = 1, padx = 10, pady = 10)

    # Ràng buộc cách nhập pin
    pin_entry.bind("<Key>", lambda event: on_key_input(event, pin_entry))

    # Nút Verify
    pin_button = Button(pin_root, text = "Verify", font = ('Cambria', 12), command = lambda:verifyPin(pin_root, root), 
                        bg = 'green', fg = 'black', padx = 20, pady = 10)
    pin_button.grid(row = 3, column = 1, pady = 20, sticky = 'n')

    # Đặt cấu hình lưới để các cột có kích thước đều
    pin_root.grid_columnconfigure(0, weight = 1)
    pin_root.grid_columnconfigure(1, weight = 1)
    pin_root.grid_columnconfigure(2, weight = 1)

def main():
    global log_area
    # Tạo GUI
    root = Tk()
    root.title("TCP/IP Server Control")
    root.geometry("1100x650")

    # Đặt màu nền cho cửa sổ chính
    root.configure(bg="gray")  # Màu xám cho toàn bộ cửa sổ

    # Khu vực hiển thị logs dạng cuộn
    log_area = scrolledtext.ScrolledText(root, state='disabled', wrap='word', height=30, font=("Arial", 12), bg="lightgray", fg="black")
    log_area.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')

    # Nút Start Server
    start_button = Button(root, text="Start Server", font=("Arial", 14), command=lambda: start_server(start_button, end_button), bg="gray", fg="black")
    start_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

    # Nút End Server
    end_button = Button(root, text="End Server", font=("Arial", 14), command=lambda: end_server(start_button, end_button), state="disabled", bg="gray", fg="black")
    end_button.grid(row=1, column=2, padx=10, pady=10, sticky="ew")

    # Cấu hình cột và hàng
    root.columnconfigure(0, weight=1)  # Cột trái
    root.columnconfigure(1, weight=1)  # Cột giữa
    root.columnconfigure(2, weight=1)  # Cột phải

    root.withdraw()
    checkPIN(root)

    # Xử lý khi người dùng đóng cửa sổ
    root.protocol("WM_DELETE_WINDOW", lambda:on_close(root))

    # Chạy GUI
    root.mainloop()

if __name__ == "__main__":
    main()