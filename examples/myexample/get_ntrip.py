import socket
import base64

HOST = "www.gnssdata.or.kr"
PORT = 2101
MOUNTPOINT = "GUMC-RTCM32"
USERNAME = "geektrck@gmail.com"
PASSWORD = "gnss"

auth = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
request = f"GET /{MOUNTPOINT} HTTP/1.1\r\nAuthorization: Basic {auth}\r\n\r\n"
print(request)
try:
    with socket.create_connection((HOST, PORT)) as s:
        print(request.encode())
        s.sendall(request.encode())
        while True:
            data = s.recv(1024)
            if not data:
                break
            print(data)
except Exception as e:
    print(e)
    if s:
        s.close