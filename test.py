url = "http://example.org/index.html"
host = url.split("/", 1)
print(host)
path = "/" + url
print(format(path))


# # This code runs only when you execute this file directly
# if __name__ == "__main__":
#     # 1. Create an instance of your URL class with a real test site
#     # (The book uses http://browser.engineering/http.html as a simple test page)
#     test_url = URL("http://browser.engineering/http.html")
    
#     print("--- Parsing Check ---")
#     print(f"Scheme: {test_url.scheme}")
#     print(f"Host:   {test_url.host}")
#     print(f"Path:   {test_url.path}")
#     print("-" * 21)

#     try:
#         # 2. Try to download the page
#         print("\nConnecting and downloading...")
#         headers, body = test_url.request()
        
#         print("\n--- Success! Response Received ---")
#         print("Headers received:", list(headers.keys()))
#         print("\nBody Content (First 250 characters):")
#         print(body[:250])
        
#     except Exception as e:
#         print("\n--- Error Occurred ---")
#         print(f"Something went wrong: {e}")