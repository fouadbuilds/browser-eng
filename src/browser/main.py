import sys
from .url import URL
from .parser import show


def load(url):
    headers, body = url.request()
    show(body)


def main():
    # fallback: If no URL is given, pass None to trigger the default local file
    if len(sys.argv) < 2:
        target_url = ""
    else:
        target_url = sys.argv[1]

    load(URL(target_url))


if __name__ == "__main__":
    main()
