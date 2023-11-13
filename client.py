#import socket
#host = "127.0.0.1"
#port = 12345
#s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#s.sendto(b"hello all", (host, port))
#s.close()

import os
response = os.popen('ping -n 1 127.0.0.1')
for line in response.readlines():
    print(line)
