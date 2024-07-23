from scapy.all import *
p=sr1(IP(dst='192.168.1.10')/ICMP()/"18181818", timeout=4)
print("ICMP: ", str(p))

p=sr1(IP(dst='192.168.1.10')/TCP(sport=19930, dport=7680),inter=0.5, retry=1, timeout=4)
print("TCP: ", str(p))
