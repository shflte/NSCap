import socket
import threading
import os
import struct


# define format of HTTP 2 frame format
class Frame:
    def __init__(self):
        self.length: int = 0
        self.type: int = 0
        self.flags: int = 0
        self.stream_id: int = 0
        self.payload: bytes = b""

    @staticmethod
    def pack_frame(type: int, flags: int, stream_id: int, payload: bytes):
        length = len(payload)
        pack_str = f"!3sBBI{length}s"
        return struct.pack(pack_str, length.to_bytes(3, 'big'), type, flags, stream_id, payload)

    def unpack_frame(self, frame: bytes):
        self.length = struct.unpack("!I", b"\x00" + frame[:3])[0]
        pack_str = f"!3sBBI{self.length}s"
        self.length, self.type, self.flags, self.stream_id, self.payload = struct.unpack(pack_str, frame)
        self.length = int.from_bytes(self.length, 'big')

    def unpack_frame_header(self, frame_header: bytes):
        self.length, self.type, self.flags, self.stream_id = struct.unpack("!3sBBI", frame_header)
        self.length = int.from_bytes(self.length, 'big')

    def print_frame(self):
        print(f"length: {self.length}")
        print(f"type: {self.type}")
        print(f"flags: {self.flags}")
        print(f"stream_id: {self.stream_id}")
        print(f"payload: {self.payload}")


class HTTPServer:
    def __init__(self, host="127.0.0.1", port=8080):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.static_path = ""

    def run(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f"Server listening on {self.host}:{self.port}")
        while True:
            client_socket, address = self.server_socket.accept()
            # create a thread to handle the request
            th = threading.Thread(target=self.handle_request, args=[client_socket])
            th.start()

    def handle_request(self, client_socket):
        while True:
            request_frame = client_socket.recv(9)
            if not request_frame:
                continue
            request = Frame()
            request.unpack_frame_header(request_frame)
            request.payload = client_socket.recv(request.length)

            # parse request
            resource, headers = self.parse_request_header(request.payload.decode("utf-8"))
            # handle request
            if resource == "/":
                self.handle_index(request, client_socket)
            elif resource.startswith("/static"):
                self.handle_static(request, client_socket, resource)

    def handle_index(self, request: Frame, client_socket): # -> header_frame, data_frame
        file_list = os.listdir(self.static_path)
        data = self.get_index_html_string(file_list)
        data_frame = Frame.pack_frame(0x0, 0x1, request.stream_id, data.encode("utf-8"))

        headers = {
            "Content-Type": "text/html",
            "content-type": "text/html",
            "Content-Length": str(len(data))
        }
        headers_str = self.get_response_header_string(headers)
        header_frame = Frame.pack_frame(0x1, 0x1, request.stream_id, headers_str.encode("utf-8"))

        # send frames
        client_socket.send(header_frame)
        client_socket.send(data_frame)

    def handle_static(self, request: Frame, client_socket, resource): # -> header_frame, data_frames
        # get file path
        file_path = self.static_path + resource[7:]
        # get file frame list
        file_frame_list = self.get_file_frame_list(file_path, request.stream_id)
        # get header frame
        headers = {
            "Content-Type": "application/octet-stream",
            "content-type": "application/octet-stream",
            "Content-Length": str(os.path.getsize(file_path))
        }
        headers_str = self.get_response_header_string(headers)
        header_frame = Frame.pack_frame(0x1, 0x1, request.stream_id, headers_str.encode("utf-8"))
        # send frames
        client_socket.send(header_frame)
        for frame in file_frame_list:
            client_socket.send(frame)

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

    def get_file_frame_list(self, file_path, stream_id) -> list:
        with open(file_path, "rb") as file:
            file_content = file.read()
        file_length = len(file_content)
        frame_list = []
        for i in range(0, file_length, 4096):
            frame = Frame.pack_frame(0x0, 0x0, stream_id, file_content[i:i+4096])
            frame_list.append(frame)
        # modify last frame's flag
        frame_list[-1] = Frame.pack_frame(0x0, 0x1, stream_id, file_content[i:i+4096])
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
        response = "HTTP/2.0 200 OK\r\n"
        for key, value in headers.items():
            response += f"{key}: {value}\r\n"
        response += "\r\n"
        return response

    def set_static(self, path):
        self.static_path = path

    def close(self):
        self.server_socket.close()

