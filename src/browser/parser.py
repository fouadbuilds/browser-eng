def lex(body):
    body = body.replace("&lt;", "<").replace("&gt;", ">")
    
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
        elif c == ">":
            in_tag = False
        elif not in_tag:
            print(c, end="")
