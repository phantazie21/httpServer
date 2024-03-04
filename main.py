from socket import *
from dataclasses import dataclass, field
from collections import defaultdict
import os

registeredSites = defaultdict(str)

@dataclass()
class HTTPResponse():
    version: str = field(default="HTTP/1.1")
    status_code: int = field(default=404)
    reason: str = field(default="Not Found")
    headers: list[str] = field(default_factory=list)
    content_length: int = field(default="100")
    content_type: str = field(default="text/html")
    body: bytes = field(default=b"<html><body>This page is not found...</body></html>")

@dataclass()
class HTTPRequest:
    url: str = field(default="")
    host: str = field(default="")
    method: str = field(default="")
    cookies: str = field(default="")
    user_agent: str = field(default="")
    accept: str = field(default="")

def registerSite(name, fileLocation):
    if os.path.exists(fileLocation):
        registeredSites[name] = fileLocation
        return True
    return False

def dataToHTTPRequest(data, debug=True):
    ret = HTTPRequest()
    lines = data.split("\n")
    if len(lines) < 1:
        return None
    if debug:
        print(f"REQUEST: {lines[0]}")
    ret.method = lines[0].split(" ")[0]
    ret.url = lines[0].split(" ")[1]
    for line in lines:
        words = line.split()
        if not words:
            continue
        if words[0] == "Host:":
            ret.host = words[1]
        elif words[0] == "User-Agent:":
            ret.user_agent = words[1:]
        elif words[0] == "Cookie:":
            ret.cookies = words[1:]
        elif words[0] == "Accept:":
            ret.accept = words[1:]
    return ret

def handleHTTPRequest(request, debug=True):
    response = HTTPResponse()
    if registeredSites[request.url]:
        response.status_code = 200
        response.reason = "OK"
        response.body = open(registeredSites[request.url], "rb").read()
        _, ext = os.path.splitext(request.url)
        ext = ext[1:]
        if ext != "jpg" and ext != "jpeg" and ext != "png" and ext != "gif" and ext != "webp":
            if "css" in request.accept[0]:
                response.content_type = "text/css"
        else:
            response.content_type = f"image/{ext}"
        
    ret = f"{response.version} {response.status_code} {response.reason}\r\n"
    if debug:
        print(f"RESPONSE: {ret}")
    for header in response.headers:
        ret += f"{header}\r\n"
    ret += f"Content-Length: {len(response.body)}\r\n"
    ret += f"Content-Type: {response.content_type}\r\n\r\n"
    ret = ret.encode() + response.body
    return ret

def run(imagespath=f"{os.getcwd()}\\images",scriptspath=f"{os.getcwd()}\\scripts", stylespath=f"{os.getcwd()}\\styles", ip="localhost", port=8080, max_connections=5, debug=True):
    print(f"Starting server on {ip}:{port}")
    if debug:
        print("DEBUG MODE IS ON!")
    try:
        images = [f for f in os.listdir(imagespath) if os.path.isfile(os.path.join(imagespath, f))]
        for image in images:
            registeredSites[f"/{image}"] = os.path.join(imagespath, image)
    except Exception as e:
        print(f"Couldn't load images... (ERROR: {e})")
    try:
        scripts = [f for f in os.listdir(scriptspath) if os.path.isfile(os.path.join(scriptspath, f))]
        for script in scripts:
            registeredSites[f"/{script}"] = os.path.join(scriptspath, script)
    except Exception as e:
        print(f"Couldn't load scripts... (ERROR: {e})")
    try:
        styles = [f for f in os.listdir(stylespath) if os.path.isfile(os.path.join(stylespath, f))]
        for style in styles:
            registeredSites[f"/{style}"] = os.path.join(stylespath, style)
    except Exception as e:
        print(f"Couldn't load styles... (ERROR: {e})")
    registeredSites["/"] = f"{os.getcwd()}\\index.html" #JUST FOR TESTING
    print(registeredSites)
    server = socket(AF_INET, SOCK_STREAM)
    try:
        server.bind((ip, port))
        server.listen(max_connections)
        while (1):
            (client, address) = server.accept()
            data = client.recv(5000).decode()
            if data:
                request = dataToHTTPRequest(data, debug)
                response = handleHTTPRequest(request, debug)
                client.sendall(response)
            client.shutdown(SHUT_WR)
    except KeyboardInterrupt:
        print("Shutting down the server...\n")
    except Exception as e:
        print(f"Error: {e}")
    server.close()

if __name__ == "__main__":
    run()