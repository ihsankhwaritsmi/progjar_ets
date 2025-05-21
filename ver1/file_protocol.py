import json
import logging
import shlex

from file_interface import FileInterface

"""
* class FileProtocol bertugas untuk memproses 
data yang masuk, dan menerjemahkannya apakah sesuai dengan
protokol/aturan yang dibuat

* data yang masuk dari client adalah dalam bentuk bytes yang 
pada akhirnya akan diproses dalam bentuk string

* class FileProtocol akan memproses data yang masuk dalam bentuk
string
"""


class FileProtocol:
    def __init__(self):
        self.file = FileInterface()

    def proses_string(self, string_datamasuk=""):
        logging.warning(f"string diproses: {string_datamasuk}")
        # c = shlex.split(string_datamasuk.lower())
        try:
            c = shlex.split(string_datamasuk)
            c_request = c[0].lower().strip()
            logging.warning(f"memproses request: {c_request}")
            params = [x for x in c[1:]]
            if c_request == "upload":
                try:
                    max_workers = int(params[-1])
                    params = params[:-1]
                except (IndexError, ValueError):
                    max_workers = 2  # Default value
                cl = getattr(self.file, c_request)(params, max_workers=max_workers)
            else:
                cl = getattr(self.file, c_request)(params)
            return json.dumps(cl)
        except Exception as e:
            return json.dumps(dict(status="ERROR", data=str(e)))


if __name__ == "__main__":
    # contoh pemakaian
    fp = FileProtocol()
    print(fp.proses_string("LIST"))
    print(fp.proses_string("GET pokijan.jpg"))
