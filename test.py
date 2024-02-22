import scapy.all as scapy
ip = scapy.IP(src="172.22.15.184", dst="172.22.15.42")
tcp = scapy.TCP(sport=30000, dport=80, flags="S", seq=1)
packet = ip/tcp
p = scapy.sr1(packet, inter=1, timeout=4)
p.show()
