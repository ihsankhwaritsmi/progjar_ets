from socket import *
import socket
import threading
import logging
import argparse
from concurrent.futures import ThreadPoolExecutor

from file_protocol import FileProtocol

fp = FileProtocol()


class ProcessTheClient:
    def __init__(self, connection, address, max_workers=2):
        self.connection = connection
        self.address = address
        self.max_workers = max_workers

    def process(self):
        buffer = ""
        while True:
            data = self.connection.recv(1024)
            if data:
                buffer += data.decode()
                if "\r\n\r\n" in buffer:
                    break
            else:
                break

        hasil = fp.proses_string(buffer.strip())
        hasil = hasil + "\r\n\r\n"
        self.connection.sendall(hasil.encode())
        self.connection.close()


class Server(threading.Thread):
    def __init__(self, ipaddress="0.0.0.0", port=8889, max_workers=2):
        self.ipinfo = (ipaddress, port)
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        threading.Thread.__init__(self)

    def run(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(1)
        while True:
            self.connection, self.client_address = self.my_socket.accept()
            logging.warning(f"connection from {self.client_address}")

            client = ProcessTheClient(
                self.connection, self.client_address, max_workers=self.max_workers
            )
            self.executor.submit(client.process)
            self.the_clients.append(client)
        self.executor.shutdown(wait=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="File Server with Thread Pool")
    parser.add_argument(
        "--max_workers", type=int, default=2, help="Maximum number of worker threads"
    )
    args = parser.parse_args()
    svr = Server(ipaddress="0.0.0.0", port=6789, max_workers=args.max_workers)
    svr.start()
