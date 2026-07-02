# Implimenting telnet in python


import socket
import ssl


class URL:
    def __init__(self, url):
        # The __init__ method is Python’s peculiar syntax for class constructors, and the self
        # parameter, which you must always make the first parameter of any method
        self.scheme, url = url.split("://", 1)
        assert self.scheme in ["http", "https"]

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
        s = socket.socket(
            family=socket.AF_INET,
            # A socket has an address family,
            # which tells you how to find the other computer.
            # Address families have names that begin with AF. We want AF_INET, but for
            # example AF_BLUETOOTH is another.
            type=socket.SOCK_STREAM,
            # A socket has a type, which describes the sort of conversation that’s going to happen. Types have names that begin with SOCK. We want SOCK_STREAM, which
            # means each computer can send arbitrary amounts of data
            proto=socket.IPPROTO_TCP,
            # A socket has a protocol, which describes the steps by which the two computers
            # will establish a connection. Protocols have names that depend on the address
            # family, but we want IPPROTO_TCP.
        )
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        s.connect((self.host, self.port))
        #  you need to tell it to connect to the other computer

        # Use a dictionary to manage request headers
        request_headers = {
            "Host": self.host,
            "Connection": "close",
            "User-Agent": "fouaden Browser",
        }

        request = f"GET {self.path} HTTP/1.1\r\n"

        # Loop through the dictionary to cleanly build the headers string
        for header, value in request_headers.items():
            request += f"{header}: {value}\r\n"
        request += "\r\n"
        s.send(request.encode("utf8"))

        response = s.makefile("r", encoding="utf8", newline="\r\n")

        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n" or line == "\n":
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

            assert "transfer-encoding" not in response_headers
            assert "content-encoding" not in response_headers

        content = response.read()
        s.close()
        # It’s the body that we’re going to display, so let’s return that:

        return response_headers, content
