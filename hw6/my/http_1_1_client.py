import socket
import os


class HTTPClient(): # For HTTP/1.X
    def __init__(self) -> None:
        self.sock = None

    @staticmethod
    def parse_url(url):
        if "http://" in url:
            url = url.replace("http://", "")
        parts = url.split("/")

        host = parts[0]

        # Split the host into hostname and port number
        host_parts = host.split(":")
        hostname = host_parts[0]  # The first part is the hostname

        if len(host_parts) > 1:
            port = int(host_parts[1])  # The second part is the port number
        else:
            port = 80  # Default port is 80 for HTTP

        # Join the remaining parts as the path
        path = "/" + "/".join(parts[1:])

        return hostname, port, path

    def form_request(self, path, headers=None, body=None):
        request = f"GET {path} HTTP/1.1\r\nContent-Length: 0\r\n"
        if headers:
            for key, value in headers.items():
                request += f"{key}: {value}\r\n"
        request += "\r\n"
        if body:
            request += body
        return request

    def get(self, url, headers=None, stream=False):
        host, port, path = self.parse_url(url)
        if self.sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host, port))

        # Send the request and return the response
        print(self.form_request(path, headers=headers).encode())
        self.sock.send(self.form_request(path, headers=headers).encode())
        response = Response(self.sock, stream)

        # If stream=True, the response should be returned immediately after the full headers have been received.
        return response


class Response():
    def __init__(self, socket, stream) -> None:
        self.socket = socket
        self.stream = stream

        # fields
        self.version = "" # e.g., "HTTP/1.1"
        self.status = ""  # e.g., "200 OK"
        self.headers = {} # e.g., {content-type: application/json}
        self.body = b""  # e.g. "{'id': '123', 'key':'456'}"
        self.body_length = 0
        self.complete = False
        self.response_bytes = b""
        self.byte_sent = 0

        self.socket.settimeout(1)
        while True:
            try:
                recved = self.socket.recv(4096)
                self.response_bytes += recved
            except:
                print("timeout")
                break

        self.parse_response()

    @staticmethod
    def parse_headers(headers_str) -> dict:
        headers = {}
        for header in headers_str.split("\r\n"):
            if ":" in header:
                key, value = header.split(": ", 1)
                headers[key] = value
        return headers
 
    def parse_response(self):
        # trim GET line
        if "\r\n" in self.response_bytes.decode():
            get_line, rest = self.response_bytes.decode().split("\r\n", 1)
            self.response_bytes = rest.encode()

        # parse headers and body
        if "\r\n\r\n" in self.response_bytes.decode():
            headers_str, body = self.response_bytes.decode().split("\r\n\r\n", 1)
            self.headers = Response.parse_headers(headers_str)
            self.body = body.encode()
            self.body_length = len(self.body)

    def get_full_body(self): # used for handling short body
        if self.stream or not self.complete:
            return None
        return self.body # the full content of HTTP response body

    def get_stream_content(self): # used for receiving stream content
        if not self.stream or self.complete:
            return None
        # iteratively return the content of HTTP response body,
        # if there's still remaining content.
        # send 4096 bytes each time
        if self.byte_sent < self.body_length:
            content = self.body[self.byte_sent:self.byte_sent+4096]
            self.byte_sent += 4096
            return content
        else:
            self.complete = True
            return None


