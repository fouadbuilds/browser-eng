import sys
from .url import URL
from .parser import show


def load(url_string):
    # Check if the user wants to view the source code
    view_source = False
    if url_string.startswith("view-source:"):
        view_source = True
        # Strip "view-source:" from the URL string so the URL class can parse the rest normally
        url_string = url_string.split("view-source:", 1)[1]

    url_instance = URL(url_string)
    headers, body = url_instance.request()

    if view_source:
        body = body.replace("&lt;", "<").replace("&gt;", ">")
        print(body)
    else:
        show(body)


def main():
    # Fallback assignment happens inside URL class automatically
    target_url = sys.argv[1] if len(sys.argv) > 1 else ""
    load(target_url)


if __name__ == "__main__":
    main()
        