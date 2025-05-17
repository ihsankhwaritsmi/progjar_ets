import socket
import json
import base64
import logging

server_address = ("0.0.0.0", 7777)


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


def remote_upload(filepath=""):
    import os

    if not os.path.isfile(filepath):
        print(f"File '{filepath}' tidak ditemukan.")
        return False

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
    server_address = ("172.16.16.101", 6789)
    remote_list()
    # remote_get('donalbebek.png')
    # remote_upload('shrek.jpg')
    remote_delete("shrek.jpg")
