import os, sys
import time
import json
import argparse
import selenium
from config import config
from config import text
from config import exit_code
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
from pyvirtualdisplay import Display
display = Display(visible=0, size=(800, 800))  
display.start()


def GetElementExistance(xpath):
    try:
        browser.find_element(by = By.XPATH, value = xpath)

        return True

    except:

        return False


def LoginMessage():
    loginErrorMsg_xpath = "//form/div/div/div/div/div"
    loginErrorPuzzle_xpath = "//aside/div/div/div/button"
    txtUseLink_xpath = '//*[@id="main"]/div/div[2]/div/div/div/div[1]/div/div[2]/div/button/div[2]'

    if GetElementExistance(loginErrorMsg_xpath):
        loginErrorMsg = browser.find_element(by = By.XPATH, value = loginErrorMsg_xpath)
        if loginErrorMsg.text in text.txtWrongPasswords:
            print("Login failed: wrong password.")

            return exit_code.EXIT_CODE_WRONG_PASSWORD
    
    elif GetElementExistance(loginErrorPuzzle_xpath):
        loginErrorPuzzle = browser.find_element(by = By.XPATH, value = loginErrorPuzzle_xpath)
        if loginErrorPuzzle.text == text.txtPlayPuzzle:
            print("Login failed: I cannot solve the puzzle.")

            return exit_code.EXIT_CODE_CANNOT_SOLVE_PUZZLE
    
    elif GetElementExistance(txtUseLink_xpath):
        Text = browser.find_element(by = By.XPATH, value = txtUseLink_xpath)
        if Text.text == text.txtUseLink:
            print("Login failed: please login via SMS.")

            return exit_code.EXIT_CODE_NEED_SMS_AUTH

        elif Text.text == text.txtEmailAuth:
            print("Login failed: need email Auth.")

            return exit_code.EXIT_CODE_NEED_EMAIL_AUTH


def UserLogin():
    print('Start to login shopee.')
    print('Try to login by username and password.')
    inputUsername = browser.find_element(by = By.NAME, value = "loginKey")
    inputUsername.send_keys(userName)
    inputPassword = browser.find_element(by = By.NAME, value = "password")
    inputPassword.send_keys(userPassword)

    btnLogin = WebDriverWait(browser, config.TIMEOUT_OPERATION).until(EC.element_to_be_clickable((By.XPATH,  "//button[text()='登入']")))
    btnLogin.click()

    for i in range(6):
        print("Wait for second {}...".format(i), end = "\r", flush = True)
        time.sleep(1)

    loginMessageResult = LoginMessage()
    
    return loginMessageResult
    

def TryLoginWithSmsLink():
    # Wait until the '使用連結驗證' is available.
    btnLoginWithLink = WebDriverWait(browser, config.TIMEOUT_OPERATION).until(EC.element_to_be_clickable((By.XPATH,  '//*[@id="main"]/div/div[2]/div/div/div/div[1]/div/div[2]/div/button')))
    btnLoginWithLink.click()

    WebDriverWait(browser, config.TIMEOUT_OPERATION).until(lambda driver: driver.current_url == "https://shopee.tw/verify/link")
    
    tooMuchTry_xpath = '//*[@id="main"]/div/div[2]/div/div/div/div[2]'
    if (GetElementExistance(tooMuchTry_xpath)):
        tooMuchTry = browser.find_element(by = By.XPATH, value = tooMuchTry_xpath)
        if text.txtTooMuchTry in tooMuchTry.text:
            print("Cannot use SMS link to login: reach daily limits.")

            return exit_code.EXIT_CODE_TOO_MUCH_TRY
    else:
        print("An SMS message is sent to your mobile. Once you click the link I will keep going. I will wait for you and please complete it in 10 minutes.")

        try:
            print("Wait for the login SMS authorization to be granted....")
            # loginStatus = WebDriverWait(browser, waitTimeout).until(EC.url_matches(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'))
            loginStatus = WebDriverWait(browser, config.TIMEOUT_OPERATION).until(EC.url_matches(r'http[s]?://shopee.tw/shopee-coins(\?.*)?$'))

            print("Login Success")

            return exit_code.EXIT_CODE_SUCCESS

        except:
            print("Login Fails")

            return exit_code.EXIT_CODE_LOGIN_DENIED


def SaveCookies():
    print("Save cookies.")
    cookies = browser.get_cookies()
    # print("Show Cookie : {}".format(cookies))
    
    for i in range(len(cookies)):
        data = {}
        data['name'] = cookies[i]['name']
        data['value'] = cookies[i]['value']
        listCookies.append(data)
    # print("Type : {}, {}".format(type(cookies_json), cookies_json))
    jsonCookies = json.dumps(listCookies)
    # print("Type : {}, {}".format(type(jsonCookies), jsonCookies))
    with open(cookiesFilePath,'w') as f:
        f.write(jsonCookies)


def LoadCookies():
    with open(cookiesFilePath) as f:
        cookies = json.load(f)
    browser.get(text.shopeeHomeUrl)

    for cookie in cookies:
        browser.add_cookie(cookie)
    browser.refresh()


def TryReceiveCoin():
    print("Check if coin is already received today.")
    
    btnReceiveCoin_xpath = '//*[@id="main"]/div/div[2]/div/main/section[1]/div[1]/div/section/div[2]/button'
    
    if GetElementExistance(btnReceiveCoin_xpath):
        btnReceiveCoin = browser.find_element(by = By.XPATH, value = btnReceiveCoin_xpath)
        if text.txtReceiveCoin in btnReceiveCoin.text:
            print(btnReceiveCoin.text)
            btnReceiveCoin.click()
        elif text.txtCoinReceived in btnReceiveCoin.text:
            print(btnReceiveCoin.text)


def LoginSuccess():
    SaveCookies()
    TryReceiveCoin()


def OpenBrowser():
    isCookieFileExist = os.path.isfile(cookiesFilePath)
    if (isCookieFileExist):
        print("Start to load cookies.")
        LoadCookies()
        
        for i in range(6):
            print("Redirect to Coin url ! Wait for second {}...".format(i), end="\r", flush = True)
            time.sleep(1)
        print("")

        browser.get(text.urlCoin)

        for i in range(6):
            print("Wait for second {}...".format(i), end="\r", flush = True)
            time.sleep(1)
        print("")
        TryReceiveCoin()
    else:
        print("No cookies given. Will try to login using username and password.")
        browser.get(text.shopeeCoinsLoginUrl)
        try:
            elementPresent = EC.presence_of_element_located((By.NAME, 'loginKey'))
            WebDriverWait(browser, config.TIMEOUT_OPERATION).until(elementPresent)
            print("Page is ready!")

            loginMessageResult = UserLogin()
            print("Result code : {}".format(loginMessageResult))

            if loginMessageResult == exit_code.EXIT_CODE_NEED_SMS_AUTH:
                liginStatusResult = TryLoginWithSmsLink()

                if (liginStatusResult == exit_code.EXIT_CODE_SUCCESS):
                    for i in range(6):
                        print("Login permitted. Wait for second {}...".format(i), end="\r", flush = True)
                        time.sleep(1)
                    LoginSuccess()

                elif (liginStatusResult == exit_code.EXIT_CODE_LOGIN_DENIED):
                    print("Login denied.")

        except TimeoutException:
            print("Loading took too much time!")

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', '-u', type=str, required=True,  help='Text for shopee username')
    parser.add_argument('--password', '-p', type=str, required=True,  help='Text for shopee password')

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    userName = args.username
    userPassword = args.password

    cookiesFilePath = "./cookies/cookies.json"
    listCookies = []

    chromedriver_autoinstaller.install()

    options = Options()
    # options.add_argument("--incognito")
    options.add_argument('--start-maximized')
    options.add_argument('--ignore-certificate-errors')
    # options.add_argument('--headless')
    # options.add_argument('--disable-extensions')
    # options.add_argument('--no-sandbox')
    # options.add_argument('--disable-dev-shm-usage')
    # options.add_argument('--disable-gpu')
    # options.add_argument('--lang=zh-TW')
    # options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    # browser = webdriver.Chrome('./webdriver/chromedriver')
    # browser = webdriver.Chrome(ChromeDriverManager().install())

    print("username : {}".format(userName))
    print("password : {}".format(userPassword))

    OpenBrowser()

