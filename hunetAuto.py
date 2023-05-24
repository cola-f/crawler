from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert

import pyautogui
import time

userId = pyautogui.prompt(title='ID를 입력하세요', text='휴넷 ID를 입력해라 아마 사번일것임.')
userPw = pyautogui.password(title='PW를 입력하세요.', text='PW를 입력해라 틀리면 확인하고 다시 ㄱㄱ')

driver = webdriver.Chrome("./chromedriver_win32/chromedriver")
driver.set_window_size(1920, 1080)

driver.get("https://iwest.hunet.co.kr/")
driver.implicitly_wait(10)

driver.find_element(By.ID, "ID").send_keys(userId)
driver.find_element(By.ID, "PW").send_keys(userPw)
driver.find_element(By.CLASS_NAME, "btn-login").click()

driver.find_element(By.XPATH, "/html/body/div[4]/ul/li[11]/a").send_keys(Keys.RETURN)
print(driver.window_handles)

for index in range(1, 8):
    완료여부_addr = "/html/body/div[6]/div[1]/table/tbody/tr["+str(index)+"]/td[4]/strong"
    완료여부 = driver.find_element(By.XPATH, 완료여부_addr).text
    if "학습중" in 완료여부:
        driver.find_element(By.XPATH, "/html/body/div[6]/div[1]/table/tbody/tr[" + str(index) + "]/td[5]/a").send_keys(Keys.RETURN)
        print(driver.window_handles)
        driver.switch_to.window(driver.window_handles[1])
        if "100" in driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div[9]/div[1]/div[1]/div[2]/strong").text:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            continue
        driver.find_element(By.XPATH, "/html/body/div[1]/div[2]/div[8]/a").send_keys(Keys.RETURN)
        print(driver.window_handles)
        driver.switch_to.window(driver.window_handles[2])

        while 1:
            try:
                alert = Alert(driver)
                print(alert.text)
                alert.accept()
                if "마지막" in alert.text:
                    driver.close()
                    driver.switch_to.window(driver.window_handles[1])
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                time.sleep(5)
            except:
                #iframe_main = driver.find_element(By.ID, "main")
                #print("iframe_main: "+str(iframe_main))
                #driver.switch_to.frame(iframe_main)
                #print("iframe_main: "+str(iframe_main))
                #driver.execute_script("document.getElementsByTagName(\"video\")[0].playbackRate=14;")
                #driver.switch_to.default_content()
                time.sleep(5)

        time.sleep(1024)
exit()
