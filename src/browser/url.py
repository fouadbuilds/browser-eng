import os
import socket
import ssl
import time

# Persistent socket connections (Exercise 1.6)
SOCKET_CACHE = {}

# --- EXERCISE 1.8: Global Memory Cache ---
# Structure: { url_string: (expiration_timestamp, headers_dict, body_string) }
HTTP_CACHE = {}

class URL:
    def __init__(self, url):
        # We store the raw URL string to use as our unique cache key
        self.raw_url = url if url else "file://test.html"

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
        """Fetches network data with Keep-Alive and Cache-Control handling."""
        current_time = time.time()

        # --- EXERCISE 1.8: Check Cache Before Network Hit ---
        if self.raw_url in HTTP_CACHE:
            expire_time, cached_headers, cached_body = HTTP_CACHE[self.raw_url]
            if current_time < expire_time:
                print(f"⚡ [CACHE HIT] Serving fresh local copy for: {self.raw_url}")
                return cached_headers, cached_body
            else:
                print(f"[CACHE EXPIRED] Stale data found for: {self.raw_url}. Re-fetching...")
                del HTTP_CACHE[self.raw_url]

        # Manage Keep-Alive persistent sockets
        socket_key = (self.host, self.port)
        s = None

        if socket_key in SOCKET_CACHE:
            s = SOCKET_CACHE[socket_key]
            try:
                s.setblocking(False)
                peek = s.recv(1, socket.MSG_PEEK)
                if peek == b"": 
                    s.close()
                    s = None
            except BlockingIOError:
                pass 
            except Exception:
                s = None
            finally:
                if s:
                    s.setblocking(True)

        if s is None:
            s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)
            s.connect((self.host, self.port))
            SOCKET_CACHE[socket_key] = s

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
            s = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM, proto=socket.IPPROTO_TCP)
            if self.scheme == "https":
                ctx = ssl.create_default_context()
                s = ctx.wrap_socket(s, server_hostname=self.host)
            s.connect((self.host, self.port))
            SOCKET_CACHE[socket_key] = s
            s.send(request.encode("utf8"))

        response = s.makefile("rb")
        statusline = response.readline().decode("utf8")
        version, status, explanation = statusline.split(" ", 2)
        
        response_headers = {}
        while True:
            line = response.readline().decode("utf8")
            if line in ["\r\n", "\n"]:
                break
            if ":" not in line:
                continue
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        if "content-length" in response_headers:
            length = int(response_headers["content-length"])
            content_bytes = response.read(length)
        else:
            content_bytes = response.read()
            s.close()
            if socket_key in SOCKET_CACHE:
                del SOCKET_CACHE[socket_key]

        content = content_bytes.decode("utf8")

        # --- EXERCISE 1.8: Evaluate Cache-Control Headers ---
        # Rule 1: Must be HTTP 200 OK success
        if status == "200":
            cache_control = response_headers.get("cache-control", "").lower()
            
            # Rule 2: If 'no-store' is specified, do not cache
            if "no-store" not in cache_control:
                max_age = 0
                has_max_age = False
                
                # Rule 3: Parse out max-age parameter value
                if "max-age" in cache_control:
                    for part in cache_control.split(","):
                        part = part.strip()
                        if part.startswith("max-age="):
                            try:
                                max_age = int(part.split("=")[1])
                                has_max_age = True
                            except ValueError:
                                pass

                # If the server provides a max-age value, commit it to memory
                if has_max_age and max_age > 0:
                    expiration_timestamp = current_time + max_age
                    HTTP_CACHE[self.raw_url] = (expiration_timestamp, response_headers, content)
                    print(f"[CACHE STORED] Cached resource for {max_age}s: {self.raw_url}")

        return response_headers, content