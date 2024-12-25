import socket
import os
import time
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox

# Cấu hình client
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 65432

def upload_file(client_socket, filepath,parent_window):
    if not os.path.exists(filepath):
        messagebox.showerror("Lỗi", f"Path {filepath} not found",parent=parent_window)
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
        messagebox.showinfo("Thông báo", client_socket.recv(1024).decode('utf-8'),parent=parent_window)
        
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
        messagebox.showinfo("Thông báo!",client_socket.recv(1024).decode('utf-8'),parent=parent_window)

def download_file(client_socket, filename, download_path,parent_window):
    client_socket.send(f"download {filename}".encode())
    response = client_socket.recv(1024).decode()
   
    if response.startswith("READY"):
        #Lấy kích thước file do bên server gửi về 
        _, file_size = response.split(" ")
        file_size = int(file_size)
        if not os.path.isdir(download_path):
            os.makedirs(download_path)
        if(os.path.isfile(filename)):
            filename = os.path.basename(filename)
            file_path = os.path.join(download_path, filename)
        else:
            filename = f"{filename}.zip"
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
        def is_zip_file(filepath):
         # Kiểm tra phần mở rộng của file
            return os.path.splitext(filepath)[1].lower() == '.zip'
        if is_zip_file(file_path):
            messagebox.showinfo("Thông báo",f"Folder {filename} downloaded successfully",parent=parent_window)
        else:
            messagebox.showinfo("Thông báo",f"File {filename} downloaded successfully",parent=parent_window)
    else:
        messagebox.showinfo("Thông báo",response,parent=parent_window)

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    ip_address = client_socket.getsockname()[1]  # Lấy địa chỉ IP của client
    print("Connected to server")

    # Gửi mã pin
    client_socket.send(f"1234".encode('utf-8'))
    pin = client_socket.recv(1024).decode('utf-8')
    if pin != "READY":
        client_socket.close()
        print("PIN wrong!")
        time.sleep(10)
        return

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
        def browse_upload(upload):
            # Mở hộp thoại chọn tệp
            file_path = filedialog.askopenfilename(title="Chọn tệp để upload", filetypes=[("All files", "*.*")])  # Chọn tệp bất kỳ
            
            if file_path:  # Nếu có chọn tệp
                upload.delete(0, END)  # Xóa nội dung cũ
                upload.insert(0, file_path)  # Điền đường dẫn của tệp vào ô nhập

        def browse_upload_folder(upload):
            # Mở hộp thoại chọn thư mục
            folder_path = filedialog.askdirectory(title="Chọn thư mục để upload")  # Chọn thư mục
            
            if folder_path:  # Nếu có chọn thư mục
                upload.delete(0, END)  # Xóa nội dung cũ
                upload.insert(0, folder_path)  # Điền đường dẫn của thư mục vào ô nhập

        def browse_download(download):
            file_path = filedialog.askopenfilename(title="Chọn tệp để download", filetypes=[("All files", "*.*")])
            if file_path:
                download.delete(0, END)  # Xóa nội dung cũ
                download.insert(0, file_path)  # Điền đường dẫn mới vào ô nhập

        def browse_download_folder(download):
            folder_path = filedialog.askdirectory(title="Chọn thư mục để download")
            if folder_path:
                download.delete(0, END)  # Xóa nội dung cũ
                download.insert(0, folder_path)  # Điền đường dẫn mới vào ô nhập

        def browse_download_path(download):
            folderpath = filedialog.askdirectory(title="Chọn thư mục lưu file")
            if folderpath:
                download.delete(0, END)  # Chỉnh sửa ô download path
                download.insert(0, folderpath)

        # Nút Upload và ô text bên cạnh
        def upload_action(upload,parent):
            filepath = upload.get()  # Lấy dữ liệu từ ô Entry
            upload_file(client_socket, filepath, parent)  # Thao tác với dữ liệu (ở đây là in ra)

        # Nút Download và ô text bên cạnh
        def download_action(download, download_path,parent):
            # Kiểm tra xem người dùng đã nhập đường dẫn tải về hay chưa
            if not download_path.get():  # Nếu ô download_path trống
                messagebox.showerror("Lỗi", "Please select a download path")
                return  # Không thực hiện tiếp tục nếu chưa chọn đường dẫn
            filename = download.get()  # Lấy dữ liệu từ ô Entry
            download_file(client_socket, filename, download_path.get(),parent)  # Thao tác với dữ liệu (ở đây là in ra)

        # Nút Upload
        def on_upload():
                root.withdraw()  
                new_window = Toplevel(root)  # Tạo cửa sổ con mới
                new_window.title("Upload")  # Đặt tiêu đề cho cửa sổ con
                new_window.geometry("800x400")  # Kích thước cửa sổ con
                Label(new_window, text="Upload", font=("Cambria", 14)).grid(row=0, column=0, columnspan=3, pady=20)
                # upload file
                upload_button = Button(new_window, text="Upload file", font=('Cambria', 12), command=lambda:upload_action(upload_entry,new_window))
                upload_button.grid(row=1, column=0, padx=10, pady=10)

                upload_entry = Entry(new_window, width=40, font=('Cambria', 12))
                upload_entry.grid(row=1, column=1, padx=10, pady=10)

                upload_browse = Button(new_window, text="Browse", font=('Cambria', 10), command=lambda:browse_upload(upload_entry))
                upload_browse.grid(row=1, column=2, padx=10, pady=10)

                # upload folder
                upload_button_folder = Button(new_window, text="Upload folder", font=('Cambria', 12), command=lambda:upload_action(upload_entry_folder,new_window))
                upload_button_folder.grid(row=2, column=0, padx=10, pady=10)

                upload_entry_folder = Entry(new_window, width=40, font=('Cambria', 12))
                upload_entry_folder.grid(row=2, column=1, padx=10, pady=10)

                upload_browse_folder = Button(new_window, text="Browse", font=('Cambria', 10), command=lambda:browse_upload_folder(upload_entry_folder))
                upload_browse_folder.grid(row=2, column=2, padx=10, pady=10)

                # Nút Close
                def on_close():
                    root.deiconify()  # Hiển thị lại cửa sổ chính (root)
                    new_window.destroy()  # Đóng cửa sổ con
                Button(new_window, text="Close", command=on_close).grid(row=5, column=1, pady=20)
                new_window.protocol("WM_DELETE_WINDOW", on_close)

        upload_button = Button(root, text="Upload", font=('Cambria', 12), command=on_upload)
        upload_button.grid(row=5, column=1, sticky='e', padx=10, pady=20)

        # Nút Download
        def on_download():
                root.withdraw()  
                new_window = Toplevel(root)  # Tạo cửa sổ con mới
                new_window.title("Download")  # Đặt tiêu đề cho cửa sổ con
                new_window.geometry("800x400")  # Kích thước cửa sổ con
                Label(new_window, text="Download", font=("Cambria", 14)).grid(row=0, column=0, columnspan=3, pady=20)
                
                # Đường dẫn lưu file sau khi tải về
                download_path_label = Label(new_window, text="Download path:", font=("Cambria", 12))
                download_path_label.grid(row=2, column=0, padx=10, pady=5, sticky=W)

                download_path_entry = Entry(new_window, width=40, font=("Cambria", 12))
                download_path_entry.grid(row=2, column=1, padx=5, pady=5)

                download_path_browse = Button(new_window, text="Browse", font=('Cambria', 10), command=lambda:browse_download_path(download_path_entry))
                download_path_browse.grid(row=2, column=2, padx=5, pady=5)               
               
                # download file
                download_button = Button(new_window, text="Download file", font=('Cambria', 12), command=lambda:download_action(download_entry,download_path_entry,new_window))
                download_button.grid(row=3, column=0, padx=10, pady=10)

                download_entry = Entry(new_window, width=40, font=('Cambria', 12))
                download_entry.grid(row=3, column=1, padx=10, pady=10)  

                download_browse = Button(new_window, text="Browse", font=('Cambria', 10), command=lambda:browse_download(download_entry))
                download_browse.grid(row=3, column=2, padx=10, pady=10)

                # download folder
                download_button_folder = Button(new_window, text="Download folder", font=('Cambria', 12), command=lambda:download_action(download_entry_folder,download_path_entry,new_window))
                download_button_folder.grid(row=4, column=0, padx=10, pady=10)

                download_entry_folder = Entry(new_window, width=40, font=('Cambria', 12))
                download_entry_folder.grid(row=4, column=1, padx=10, pady=10)

                download_browse_folder = Button(new_window, text="Browse", font=('Cambria', 10), command=lambda:browse_download_folder(download_entry_folder))
                download_browse_folder.grid(row=4, column=2, padx=10, pady=10)

                # Nút Close
                def on_close():
                    root.deiconify()  # Hiển thị lại cửa sổ chính (root)
                    new_window.destroy()  # Đóng cửa sổ con
                Button(new_window, text="Close", command=on_close).grid(row=5, column=1, pady=20)
                new_window.protocol("WM_DELETE_WINDOW", on_close)

        download_button = Button(root, text="Download", font=('Cambria', 12), command=on_download)
        download_button.grid(row=6, column=1, sticky='e', padx=10, pady=20)

        # Nút exit
        def on_exit():
            result = messagebox.askquestion("Xác nhận thoát", "Disconnect from server?")
            if result == "yes":
                exit()
        exit_button = Button(root, text="Exit", font=('Cambria', 12), command=on_exit)
        exit_button.grid(row=7, column=1, sticky='e', padx=10, pady=20)

        # Chạy vòng lặp chính
        root.mainloop()
                
    finally:
        client_socket.close()
        print("Disconnected from server")

if __name__ == "__main__":
    main()