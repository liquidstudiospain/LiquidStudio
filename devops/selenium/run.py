import os
import sys

from colorama import Fore

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from tests.case_submit import get_all_classes


SUCCESS_TAG = '{}[SUCCESS]{}'.format(Fore.GREEN, Fore.RESET)
ERROR_TAG = '{}[ERROR]{}'.format(Fore.RED, Fore.RESET)
FATAL_TAG = '{}[FATAL]{}'.format(Fore.RED, Fore.RESET)
INFO_TAG = '{}[INFO]{}'.format(Fore.YELLOW, Fore.RESET)


def __color_test_result(status, message):
    color = Fore.GREEN if status else Fore.RED
    return '{}{}{}'.format(color, message, Fore.RESET)


def __start():
    from credentials import username, password, base_url
    # __clear_screen()
    driver = __get_web_driver()
    if driver is None:
        exit(-1)
    if not __login(driver, base_url, username, password):
        driver.close()
        exit(-1)
    all_correct = __run_tests(driver, base_url)
    driver.close()
    if all_correct:
        exit(0)
    else:
        exit(-1)

def __clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def __run_tests(driver, base_url):
    print('{} Starting tests:'.format(INFO_TAG))
    tests_results = []
    number_of_success = 0
    tests = get_all_classes()
    for test in tests:
        instance = test(driver, base_url)
        sys.stdout.write('\t- {}{}{}: '.format(Fore.CYAN, instance.test_name, Fore.RESET))
        sys.stdout.flush()
        status, message = instance.run()
        print(__color_test_result(status, message))
        number_of_success += 1 if status else 0
        tests_results.append(message)
    return len(tests_results) == number_of_success


def __get_web_driver():
    print('{} Opening WebDriver'.format(INFO_TAG))
    path_webdriver = ('selenium\\webdriver\\chromedriver.exe'
                      if os.name == 'nt' else '/usr/local/bin/chromedriver')
    options = Options()
    print(path_webdriver)
    if not os.name == 'nt':
        options.add_argument('--headless')
    # options.add_argument('--disable-gpu')
    try:
        driver = webdriver.Chrome(path_webdriver, chrome_options=options)
        return driver
    except Exception as e:
        print('{} Could not open browser, aborting'.format(FATAL_TAG))


def __login(driver, base_url, username, password):
    ''' Logs in to passed to passed environment, with passed username and password '''
    try:
        print('{} Logging in to Salesforce'.format(INFO_TAG))
        driver.get(base_url)
        assert "Salesforce" in driver.title
        driver.find_element_by_id("username").send_keys(username)
        driver.find_element_by_id("password").send_keys(password)
        driver.find_element_by_id("Login").click()
        WebDriverWait(driver, 3)
        driver.get(base_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'phHeaderLogoImage')))
        return True
    except Exception as e:
        print(e)
        print('{} Could not sign in, aborting'.format(FATAL_TAG))


if __name__ == '__main__':
    __start()
