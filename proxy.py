from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from mitmproxy import ProxyConfig, ProxyServer, Options as MitmOptions

# Mitmproxy를 사용하여 패킷을 가로채는 클래스
class MitmProxyAddon:
    def __init__(self):
        self.flow_writer = None

    def configure(self, updated):
        self.flow_writer = open('captured_flows.txt', 'wb')

    def request(self, flow):
        self.flow_writer.write(flow.request.raw_content)

    def done(self):
        if self.flow_writer is not None:
            self.flow_writer.close()

# Mitmproxy 설정
mitm_options = MitmOptions(listen_host='127.0.0.1', listen_port=8080)
mitm_proxy = ProxyServer(ProxyConfig(mitm_options=mitm_options))

# Chrome WebDriver 설정
chrome_options = Options()
chrome_options.add_argument('--proxy-server=localhost:8080')  # Mitmproxy가 동작 중인 포트

# WebDriver 시작
driver = webdriver.Chrome(options=chrome_options)

# Mitmproxy 시작
proxy_addon = MitmProxyAddon()
mitm_proxy.addons.add(proxy_addon)

# Chrome을 Mitmproxy로 연결
driver.get('http://example.com')  # 접속하고자 하는 웹페이지의 주소를 입력합니다.

# 기다림 (원하는 작업 수행)

# 종료
mitm_proxy.shutdown()
driver.quit()


#from seleniumwire import webdriver
#import time
#
#driver = webdriver.Chrome()
#driver.set_window_size(800, 600)
#driver.get("https://www.naver.com")
#driver.implicitly_wait(10)
#request = driver.wait_for_request('https://naver.com/')
#print("request: ", request)
#time.sleep(1024)
#while 1:
#    
#    for request in driver.requests:
#        if request.response:
#            print(
#                    "request.url: ", request.url,
#                    "status_code: ", request.response.status_code,
#                    "headers: ", request.response.headers['Content-Type']
#                    )
