import os
import socket
import ssl

#  Global cache to preserve open persistent sockets ---
# Key: (host, port) -> Value: socket object
SOCKET_CACHE = {}

class URL:
    def __init__(self, url):
        if not url:
            self.scheme = "file"
            self.path = os.path.abspath("test.html")
            self.host = ""
            self.port = None
            return

        if url.startswith("data:"):
            self.scheme = "data"
            self.content_type, self.data_content = url.split(",", 1)
            return

        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https", "file"]

        if self.scheme == "file":
            self.host = ""
            self.port = None
            if url.startswith("/") and len(url) > 2 and url[2] == ":":
                url = url[1:]
            self.path = os.path.abspath(url)
            return

        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        if "/" not in url:
            url = url + "/"
        
        self.host, url = url.split("/", 1)
        self.path = "/" + url

        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self):
        if self.scheme == "data":
            return {"content-type": "text/html"}, self.data_content
        if self.scheme == "file":
            return self._request_file()
        return self._request_network()

    def _request_file(self):
        fake_headers = {"content-type": "text/html", "server": "local-file-system"}
        try:
            with open(self.path, "r", encoding="utf8") as f:
                content = f.read()
            return fake_headers, content
        except FileNotFoundError:
            return fake_headers, f"<html><body><h1>404 File Not Found</h1></body></html>"

    def _request_network(self):
        """Manages Keep-Alive persistent connection sockets."""
        socket_key = (self.host, self.port)
        s = None

        # Check if we have an existing, open socket to this host
        if socket_key in SOCKET_CACHE:
            s = SOCKET_CACHE[socket_key]
            # Verify the socket is still healthy by doing a non-blocking peek
            try:
                s.setblocking(False)
                peek = s.recv(1, socket.MSG_PEEK)
                if peek == b"": # Connection was closed by server
                    s.close()
                    s = None
            except BlockingIOError:
                pass # Socket is open and silent, perfect
            except Exception:
                s = None
            finally:
                if s:
                    s.setblocking(True)

        # If no cached socket exists or it was broken, establish a fresh connection
        if s is None:
            s = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)
            s.connect((self.host, self.port))
            # Cache it immediately for future runs
            SOCKET_CACHE[socket_key] = s

        # Build request headers (Notice Connection is now keep-alive)
        request_headers = {
            "Host": self.host,
            "Connection": "keep-alive",
            "User-Agent": "MyCustomBrowser/1.0"
        }
        
        request = f"GET {self.path} HTTP/1.1\r\n"
        for header, value in request_headers.items():
            request += f"{header}: {value}\r\n"
        request += "\r\n"
        
        try:
            s.send(request.encode("utf8"))
        except Exception:
            # If the cached socket fails unexpectedly on send, rebuild it once
            s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)
            s.connect((self.host, self.port))
            SOCKET_CACHE[socket_key] = s
            s.send(request.encode("utf8"))

        # Process the stream safely
        response = s.makefile("r", encoding="utf8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)
        
        response_headers = {}
        while True:
            line = response.readline()
            if line in ["\r\n", "\n"]:
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        # CRITICAL: Read ONLY the exact number of bytes specified by Content-Length
        if "content-length" in response_headers:
            length = int(response_headers["content-length"])
            content = response.read(length)
        else:
            # Fallback if server doesn't provide it (forces socket close to read EOF)
            content = response.read()
            s.close()
            if socket_key in SOCKET_CACHE:
                del SOCKET_CACHE[socket_key]

        return response_headers, content