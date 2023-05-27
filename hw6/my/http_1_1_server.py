import socket
import threading
import os


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
            request = client_socket.recv(4096).decode()
            if not request:
                continue
            resource, headers = self.parse_request(request)
            print(f"{resource} requested")
            if resource == "/":
                response = self.handle_index()
            elif resource.startswith("/static"):
                response = self.handle_static(resource)
            else:
                response = self.build_response("404 Not Found")
            client_socket.send(response.encode())

    def handle_index(self):
        file_list = os.listdir(self.static_path)
        body = self.get_index_html_string(file_list)
        headers = {}
        headers["Content-Length"] = len(body)
        headers["Content-Type"] = "text/html"
        headers["content-type"] = "text/html"
        response = self.build_response("200 OK", headers=headers, body=body)

        return response

    def handle_static(self, resource):
        file_path = self.static_path + resource[len("/static"):]
        print(file_path)
        if os.path.isfile(file_path):
            with open(file_path, "rb") as file:
                file_content = file.read().decode()
            headers = {}
            headers["Content-Length"] = len(file_content)
            headers["Content-Type"] = "application/octet-stream"
            headers["content-type"] = "application/octet-stream"
            response = self.build_response("200 OK", headers=headers, body=file_content)

        return response

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

    @staticmethod
    def parse_request(request):
        method, resource, http_version = request.split("\r\n", 1)[0].split(" ")
        headers_list = request.split("\r\n")[1:]
        headers = dict()
        for header in headers_list:
            if header:
                key, value = header.split(": ", 1)
                headers[key] = value
        return resource, headers

    @staticmethod
    def build_response(status, headers=None, body=None):
        response = f"HTTP/1.1 {status}\r\n"
        if headers:
            for key, value in headers.items():
                response += f"{key}: {value}\r\n"
        response += "\r\n"
        if body:
            response += body
        return response

    def set_static(self, path):
        self.static_path = path

    def close(self):
        self.server_socket.close()

