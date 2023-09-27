from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert

import pyautogui
import time

userId = 'iwest@iwest.co.kr'
userPw = 'schrodin12!@'

driver = webdriver.Chrome("./chromedriver_win32/chromedriver")
driver.set_window_size(1920, 1080)

driver.get("https://edu.kiha21.or.kr")
driver.implicitly_wait(10)

driver.find_element(By.XPATH, "/html/body/div[2]/aside/ul/li[2]/a").click()
driver.find_element(By.XPATH, "/html/body/div[2]/main/div[2]/div/section/div/form/div/div/div[1]/input").send_keys(userId)
driver.find_element(By.XPATH, "/html/body/div[2]/main/div[2]/div/section/div/form/div/div/div[2]/input").send_keys(userPw)
driver.find_element(By.XPATH, "/html/body/div[2]/main/div[2]/div/section/div/form/div/div/div[4]/button").click()

driver.find_element(By.XPATH, "/html/body/div[2]/main/div[2]/div/section/div/div/div/div[3]/div/div/div[2]/ul/li[4]/div/div/button").click()
time.sleep(1024)
driver.switch_to.window(driver.window_handles[1])
for index in range(1, 7):
    driver.find_element(By.XPATH, "/html/body/div[1]/div[3]/div/div[2]/div/div/div/div[3]/div/ul/li[1]/div[3]/ul/li["+str(index)+"]/div/div/div[2]/a").click()
    time.sleep(3600)

