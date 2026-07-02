import sys
from .url import URL
from .parser import lex


def load(url_string):
    # Check and clean the view-source prefix
    view_source = False
    if url_string.startswith("view-source:"):
        view_source = True
        url_string = url_string.split("view-source:", 1)[1]

    redirect_count = 0
    max_redirects = 10
    
    # Track headers and body outside the loop so they are available after we break
    headers = {}
    body = ""

    while redirect_count < max_redirects:
        url_instance = URL(url_string)
        
        if url_instance.scheme in ["data", "file"]:
            headers, body = url_instance.request()
            break
            
        headers, body = url_instance.request()
        
        # If 'location' is in headers, we must redirect
        if "location" in headers:
            redirect_count += 1
            new_location = headers["location"]
            
            if "://" in new_location:
                url_string = new_location
            else:
                url_string = f"{url_instance.scheme}://{url_instance.host}{new_location}"
            
            print(f"-> Redirecting to: {url_string} (Hop {redirect_count})")
            # Clear headers to prevent any potential reuse leaks next iteration
            headers = {} 
            continue
        else:
            # NO LOCATION HEADER FOUND. We hit our destination! Break out immediately.
            break
    else:
        print(f"Error: Exceeded maximum redirect limit of {max_redirects} hops.")
        return

    # Now that we have broken out of the loop safely, handle rendering/view-source
    if view_source:
        body = body.replace("&lt;", "<").replace("&gt;", ">")
        print(body)
    else:
        lex(body)

def main():
    # Fallback assignment happens inside URL class automatically
    target_url = sys.argv[1] if len(sys.argv) > 1 else ""
    load(target_url)


if __name__ == "__main__":
    main()
