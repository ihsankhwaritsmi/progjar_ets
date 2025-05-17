import socket
import json
import base64
import logging
import argparse


def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning(f"sending message ")
        # sock.sendall(command_str.encode())
        sock.sendall((command_str + "\r\n\r\n").encode())
        # Look for the response, waiting until socket is done (no more data)
        data_received = ""  # empty string
        while True:
            # socket does not receive all data at once, data comes in part, need to be concatenated at the end of process
            data = sock.recv(16)
            if data:
                # data is not empty, concat with previous content
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                # no more data, stop the process by break
                break
        # at this point, data_received (string) will contain all data coming from the socket
        # to be able to use the data_received as a dict, need to load it using json.loads()
        hasil = json.loads(data_received)
        logging.warning("data received from server:")
        return hasil
    except:
        logging.warning("error during data receiving")
        return False


def remote_list():
    command_str = f"LIST"
    hasil = send_command(command_str)
    if hasil["status"] == "OK":
        print("daftar file : ")
        for nmfile in hasil["data"]:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal")
        return False


def remote_get(filename=""):
    command_str = f"GET {filename}"
    try:
        hasil = send_command(command_str)
        if hasil["status"] == "OK":
            # proses file dalam bentuk base64 ke bentuk bytes
            namafile = hasil["data_namafile"]
            isifile = base64.b64decode(hasil["data_file"])
            fp = open(namafile, "wb+")
            fp.write(isifile)
            fp.close()
            return True
        else:
            print("Gagal")
            return False
    except Exception as e:
        print(f"Download failed with exception: {e}")
        return False


def remote_upload(filepath=""):
    import os

    if not os.path.isfile(filepath):
        print(f"File '{filepath}' tidak ditemukan.")
        return False
    try:
        with open(filepath, "rb") as f:
            file_data = f.read()
        encoded_data = base64.b64encode(file_data).decode()

        filename = os.path.basename(filepath)
        # Format command upload dengan nama file dan isi base64, misal:
        # UPLOAD nama_file base64encodedstring
        # Karena base64 bisa sangat panjang, lebih baik gunakan kutipan agar parsing lebih aman
        command_str = f'UPLOAD "{filename}" "{encoded_data}"'

        hasil = send_command(command_str)
        if hasil and hasil.get("status") == "OK":
            print(f"File '{filename}' berhasil diupload.")
            return True
        else:
            print("Upload gagal.")
            return False
    except Exception as e:
        print(f"Upload failed with exception: {e}")
        return False


def remote_delete(filename=""):
    if filename == "":
        print("Nama file harus diisi.")
        return False

    command_str = f'DELETE "{filename}"'
    hasil = send_command(command_str)
    if hasil and hasil.get("status") == "OK":
        print(f"File '{filename}' berhasil dihapus dari server.")
        return True
    else:
        print(f"Gagal menghapus file '{filename}'.")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="File Client CLI")
    parser.add_argument(
        "--operation",
        type=str,
        default="upload",
        choices=["upload", "download"],
        help="Operation to perform (upload or download)",
    )
    parser.add_argument(
        "--file_size",
        type=int,
        default=10,
        choices=[10, 50, 100],
        help="File size in MB (10, 50, or 100)",
    )
    parser.add_argument(
        "--client_workers",
        type=int,
        default=1,
        choices=[1, 5, 50],
        help="Number of client worker threads",
    )
    parser.add_argument(
        "--server_address",
        type=str,
        default="172.16.16.101:6789",
        help="Server address (ip:port)",
    )
    args = parser.parse_args()

    server_address = tuple(args.server_address.split(":"))
    server_address = (server_address[0], int(server_address[1]))

    # remote_list()
    # remote_get('donalbebek.png')
    # remote_upload('shrek.jpg')
    # remote_delete("shrek.jpg")

    server_workers = [1, 5, 50]
    operations = ["upload", "download"]
    file_sizes = [10, 50, 100]
    client_workers = [1, 5, 50]

    for operation in operations:
        for file_size in file_sizes:
            for client_worker in client_workers:
                for server_worker in server_workers:
                    print(
                        f"Operation: {operation}, File Size: {file_size}MB, Client Workers: {client_worker}, Server Workers: {server_worker}"
                    )
                    filename = f"file_{file_size}MB.bin"
                    filepath = filename  # Assuming files are in the same directory

                    import time

                    start_time = time.time()
                    if operation == "upload":
                        success = remote_upload(filepath)
                    elif operation == "download":
                        success = remote_get(filename)
                    end_time = time.time()
                    total_time = end_time - start_time
                    file_size_bytes = file_size * 1024 * 1024  # Convert MB to bytes
                    throughput = file_size_bytes / total_time
                    print(
                        f"Total time: {total_time:.2f} seconds, Throughput: {throughput:.2f} bytes/second"
                    )
                    if success:
                        print("Operation successful")
                    else:
                        print("Operation failed")
