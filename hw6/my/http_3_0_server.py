import time
import socket
import threading
import os
import struct
from my.QUIC.quic_server import QUICServer


# define format of HTTP 3 frame format
class Frame:
    def __init__(self):
        self.type: int = 0
        self.length: int = 0
        self.payload: bytes = b""

    @staticmethod
    def pack_frame(type: int, payload: bytes):
        length = len(payload)
        pack_str = f"!BI{length}s"
        return struct.pack(pack_str, type, length, payload)

    def unpack_frame(self, frame_header: bytes):
        self.type, self.length = struct.unpack("!BI", frame_header[:5])
        self.payload = frame_header[5:]

    def print_frame(self):
        print(f"type: {self.type}")
        print(f"length: {self.length}")
        print(f"payload: {self.payload}")


class HTTPServer:
    def __init__(self, host="127.0.0.1", port=6789):
        self.sockaddr = (host, port)
        self.server = QUICServer()
        self.static_path = ""
        self.lock = threading.Lock()

    def run(self):
        self.server.listen(self.sockaddr)
        print(f"Server listening on {self.sockaddr}")
        self.server.accept()
        while True:
            # receive request
            print("waiting for request...")
            # type: tuple of type (stream_id, request_frame, flag)
            recved = self.server.recv()
            request = Frame()
            request.unpack_frame(recved[1])
            print("request: \n", request.payload.decode("utf-8"))

            # parse request
            resource, headers = self.parse_request_header(request.payload.decode("utf-8"))
            # handle request
            if resource == "/":
                # self.handle_index(recved[0])
                # create a new thread to handle request
                t = threading.Thread(target=self.handle_index, args=(recved[0],))
            elif resource.startswith("/static"):
                # self.handle_static(recved[0], resource)
                t = threading.Thread(target=self.handle_static, args=(recved[0], resource))

            t.start()

    def atomic_send(self, stream_id: int, frame: bytes, flag: bool):
        self.lock.acquire()
        self.server.send(stream_id, frame, flag)
        self.lock.release()

    def handle_index(self, stream_id: int): # -> header_frame, data_frame
        file_list = os.listdir(self.static_path)
        data = self.get_index_html_string(file_list)
        data_frame = Frame.pack_frame(0x0, data.encode("utf-8"))

        headers = {
            "Content-Type": "text/html",
            "content-type": "text/html",
            "Content-Length": str(len(data))
        }
        headers_str = self.get_response_header_string(headers)
        header_frame = Frame.pack_frame(0x1, headers_str.encode("utf-8"))

        # send frames
        self.atomic_send(stream_id, header_frame, True)
        self.atomic_send(stream_id, data_frame, True)

    def handle_static(self, stream_id: int, resource): # -> header_frame, data_frames
        # get file path
        file_path = self.static_path + resource[7:]
        # get file frame list
        file_frame_list = self.get_file_frame_list(file_path)
        # get header frame
        # headers = {
        #     "Content-Type": "application/octet-stream",
        #     "content-type": "application/octet-stream",
        #     "Content-Length": str(os.path.getsize(file_path))
        # }
        # headers_str = self.get_response_header_string(headers)
        # header_frame = Frame.pack_frame(0x1, headers_str.encode("utf-8"))
        # # send frames
        # self.atomic_send(stream_id, header_frame, True)
        for frame in file_frame_list:
            self.atomic_send(stream_id, frame, False)
            # print out which streams' data is sent
            print(f"stream {stream_id} data sent")
            time.sleep(0.2)

    @staticmethod
    def get_index_html_string(file_list) -> str:
        body = "<html><header></header><body>"
        for file in file_list:
            body += f'<a href="/static/{file}">{file}</a><br/>'
        # if body end with <br>, remove it
        if body.endswith("<br/>"):
            body = body[:-5]
        body += "</body></html>"
        return body

    def get_file_frame_list(self, file_path) -> list:
        with open(file_path, "rb") as file:
            file_content = file.read()
        file_length = len(file_content)
        frame_list = []
        for i in range(0, file_length, 1000):
            frame = Frame.pack_frame(0x0, file_content[i:i+1000])
            frame_list.append(frame)
        
        return frame_list

    @staticmethod
    def parse_request_header(request: str): # -> (resource: str, headers: dict)
        method, resource, http_version = request.split("\r\n", 1)[0].split(" ")
        headers_list = request.split("\r\n")[1:]
        headers = dict()
        for header in headers_list:
            if header:
                key, value = header.split(": ", 1)
                headers[key] = value
        return resource, headers

    @staticmethod
    def get_response_header_string(headers=None) -> str:
        if headers is None:
            headers = dict()
        response = "HTTP/3.0 200 OK\r\n"
        for key, value in headers.items():
            response += f"{key}: {value}\r\n"
        response += "\r\n"
        return response

    def set_static(self, path):
        self.static_path = path

    def close(self):
        self.server.close()
