import socket
import os
import time
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox

# Cấu hình client
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432

def upload_file(client_socket, filepath):
    if not os.path.exists(filepath):
        messagebox.showerror("Lỗi", f"Path {filepath} not found")
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
        messagebox.showinfo("Thông báo", client_socket.recv(1024).decode('utf-8'))
        
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

        client_socket.send(b'FOLDER_END')
        client_socket.recv(1024)
        messagebox("Thông báo!",client_socket.recv(1024).decode('utf-8'))

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

        messagebox.showinfo("Thông báo",f"File {filename} downloaded successfully")
    else:
        print(response)

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    ip_address = client_socket.getsockname()[1]  # Lấy địa chỉ IP của client
    print("Connected to server")

    try:
        # Tạo cửa sổ chính
        root = Tk()
        root.title('TCP/IP')
        root.minsize(height=500, width=500)

        # Dữ liệu mẫu (có thể thay bằng dữ liệu thực)
        server_host = SERVER_HOST
        server_port = SERVER_PORT
        address_client = ip_address

        # Hiển thị tiêu đề "Socket"
        Label(root, text='Socket', fg='red', font=('Cambria', 16), width=20).grid(row=0, column=0, columnspan=2, pady=20)

        # Thông tin Server Host
        Label(root, text="Server Host:", font=('Cambria', 12)).grid(row=1, column=0, sticky='w', padx=10)
        Label(root, text=server_host, font=('Cambria', 12), fg='blue').grid(row=1, column=1, sticky='w', padx=10)

        # Thông tin Server Port
        Label(root, text="Server Port:", font=('Cambria', 12)).grid(row=2, column=0, sticky='w', padx=10)
        Label(root, text=server_port, font=('Cambria', 12), fg='blue').grid(row=2, column=1, sticky='w', padx=10)

        # Thông tin Address Client
        Label(root, text="Address Client:", font=('Cambria', 12)).grid(row=3, column=0, sticky='w', padx=10)
        Label(root, text=address_client, font=('Cambria', 12), fg='blue').grid(row=3, column=1, sticky='w', padx=10)

        # Hàm chọn đường dẫn cho nút "Browse"
        def browse_upload():
            # Mở hộp thoại chọn tệp hoặc thư mục với tùy chọn cho phép chọn cả hai
            file_or_folder = filedialog.askopenfilename(title="Chọn tệp hoặc thư mục để upload", 
                                                        filetypes=[("All files", "*.*")])  # Chọn tệp
            
            if not file_or_folder:  # Nếu không chọn tệp (chưa chọn hoặc nhấn "Cancel"), thử chọn thư mục
                file_or_folder = filedialog.askdirectory(title="Chọn thư mục để upload")  # Chọn thư mục

            if file_or_folder:  # Nếu có lựa chọn (tệp hoặc thư mục)
                upload_entry.delete(0, END)  # Xóa nội dung cũ
                upload_entry.insert(0, file_or_folder)  # Điền đường dẫn vào ô nhập

        def browse_download():
            folderpath = filedialog.askdirectory(title="Chọn thư mục để lưu")
            if folderpath:
                download_entry.delete(0, END)  # Xóa nội dung cũ
                download_entry.insert(0, folderpath)  # Điền đường dẫn mới vào ô nhập

        # Nút Upload và ô text bên cạnh
        def upload_action():
            filepath = upload_entry.get()  # Lấy dữ liệu từ ô Entry
            upload_file(client_socket, filepath)  # Thao tác với dữ liệu (ở đây là in ra)

        upload_button = Button(root, text="Upload", font=('Cambria', 12), command=upload_action)
        upload_button.grid(row=4, column=0, padx=10, pady=10)

        upload_entry = Entry(root, font=('Cambria', 12))
        upload_entry.grid(row=4, column=1, padx=10, pady=10)

        upload_browse = Button(root, text="Browse", font=('Cambria', 10), command=browse_upload)
        upload_browse.grid(row=4, column=2, padx=10, pady=10)

        # Nút Download và ô text bên cạnh
        def download_action():
            filename = download_entry.get()  # Lấy dữ liệu từ ô Entry
            download_file(client_socket, filename)  # Thao tác với dữ liệu (ở đây là in ra)

        download_button = Button(root, text="Download", font=('Cambria', 12), command=download_action)
        download_button.grid(row=5, column=0, padx=10, pady=10)

        download_entry = Entry(root, font=('Cambria', 12))
        download_entry.grid(row=5, column=1, padx=10, pady=10)

        download_browse = Button(root, text="Browse", font=('Cambria', 10), command=browse_download)
        download_browse.grid(row=5, column=2, padx=10, pady=10)

        # Nút Exit
        def on_exit():
            messagebox.showinfo('Thông báo','Disconnect from server')
            exit()

        exit_button = Button(root, text="Exit", font=('Cambria', 12), command=on_exit)
        exit_button.grid(row=6, column=1, sticky='e', padx=10, pady=20)

        # Chạy vòng lặp chính
        root.mainloop()
                
    finally:
        client_socket.close()
        print("Disconnected from server")

if __name__ == "__main__":
    main()