import socket
import json
import base64
import logging
import argparse
import time
import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import pandas as pd


def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    try:
        sock.sendall((command_str + "\r\n\r\n").encode())
        data_received = ""
        while True:
            data = sock.recv(16)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        hasil = json.loads(data_received)
        return hasil
    except Exception as e:
        logging.warning(f"Error: {e}")
        return {"status": "ERROR", "message": str(e)}
    finally:
        sock.close()


def remote_upload(filepath, server_workers):
    try:
        with open(filepath, "rb") as f:
            file_data = f.read()
        encoded_data = base64.b64encode(file_data).decode()
        filename = os.path.basename(filepath)
        command_str = f'UPLOAD "{filename}" "{encoded_data}" {server_workers}'
        hasil = send_command(command_str)
        return hasil.get("status") == "OK"
    except Exception as e:
        logging.warning(f"Upload failed: {e}")
        return False


def remote_get(filename):
    try:
        command_str = f'GET "{filename}"'
        hasil = send_command(command_str)
        if hasil.get("status") == "OK":
            isifile = base64.b64decode(hasil["data_file"])
            with open(filename, "wb+") as fp:
                fp.write(isifile)
            return True
        return False
    except Exception as e:
        logging.warning(f"Download failed: {e}")
        return False


def run_test_case(operation, file_size, client_workers, server_workers):
    filename = f"file_{file_size}MB.bin"
    filepath = filename
    file_size_bytes = file_size * 1024 * 1024

    # Create test file if it doesn't exist
    if not os.path.exists(filepath):
        with open(filepath, "wb") as f:
            f.write(os.urandom(file_size_bytes))

    futures = []
    success_clients = 0
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=client_workers) as executor:
        for _ in range(client_workers):
            if operation == "upload":
                futures.append(executor.submit(remote_upload, filepath, server_workers))
            elif operation == "download":
                futures.append(executor.submit(remote_get, filename))

        for future in as_completed(futures):
            if future.result():
                success_clients += 1

    total_time = time.time() - start_time
    throughput = (
        (success_clients * file_size_bytes) / total_time if total_time > 0 else 0
    )

    return {
        "operation": operation,
        "volume": f"{file_size}MB",
        "client_workers": client_workers,
        "server_workers": server_workers,
        "total_time": round(total_time, 2),
        "throughput": round(throughput, 2),
        "success_clients": success_clients,
        "failed_clients": client_workers - success_clients,
        "success_servers": server_workers if success_clients > 0 else 0,
        "failed_servers": 0 if success_clients > 0 else server_workers,
    }


def main():
    parser = argparse.ArgumentParser(description="File Client Stress Test")
    parser.add_argument("--server_address", type=str, default="localhost:6789")
    args = parser.parse_args()

    global server_address
    server_address = tuple(args.server_address.split(":"))
    server_address = (server_address[0], int(server_address[1]))

    # Define test combinations
    operations = ["upload", "download"]
    file_sizes = [10, 50, 100]
    client_workers_list = [1, 5, 50]
    server_workers_list = [1, 5, 50]

    results = []
    test_num = 1

    for operation in operations:
        for file_size in file_sizes:
            for client_workers in client_workers_list:
                for server_workers in server_workers_list:
                    print(
                        f"Running Test #{test_num}: "
                        f"Op={operation}, Size={file_size}MB, "
                        f"Clients={client_workers}, Servers={server_workers}"
                    )
                    result = run_test_case(
                        operation, file_size, client_workers, server_workers
                    )
                    result["test_num"] = test_num
                    results.append(result)
                    test_num += 1

    # Save results to CSV
    df = pd.DataFrame(results)
    df.to_csv("stress_test_results.csv", index=False)
    print("\nStress test completed. Results saved to 'stress_test_results.csv'.")


if __name__ == "__main__":
    main()
