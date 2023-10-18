import socket
host = "127.0.0.1" #Server address
port = 12345 # Port of server
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print("This hostname: ", socket.gethostname())
print("This IP: ", socket.gethostbyname(socket.gethostname()))
print("This interface", socket.gethostbyname_ex(socket.gethostname()))
try:
    s.bind((host, port)) # bind server
    s.settimeout(5) #timeout 5 seconds
    data, addr = s.recvfrom(1024)
    print("received from: ", addr)
    print("obtained: ", data)
except socket.timeout:
    print("Client not connected")
finally:
    s.close()
