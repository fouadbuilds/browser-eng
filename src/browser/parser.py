
def lex(body):
    text = ""
    # body = body.repla ce("&lt;", "<").replace("&gt;", ">")
    
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            text += c
    return text
