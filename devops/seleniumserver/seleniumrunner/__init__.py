''' Selenium Runner module '''
import os
import sys
import threading
import time

from colorama import Fore, init

from seleniumrunner.tests.case_submit import get_all_classes

from seleniumrunner.driver import Driver
from seleniumrunner.credentials import USERNAME, PASSWORD, BASE_URL
from seleniumrunner.tests import TestResultBundle

from utils import PATH_WEBDRIVER, INFO_TAG, FATAL_TAG, _color_test_result


class SeleniumRunner:
    ''' Selenium Runner Implementation '''
    def __init__(self, thread_number, verbose, webdriver_path=PATH_WEBDRIVER):
        print(f'{INFO_TAG} Launching SeleniumRunner with {thread_number} thread(s)')
        try:
            # if not file_exists(webdriver_path):
            # raise WebDriverNotFoundException
            self.webdriver_path = webdriver_path
            self.drivers = Driver(BASE_URL) * thread_number
            self.verbose = verbose
            self.__threaded_sign_in()
            print(f'{INFO_TAG} All Drivers started succesfully')
        except Exception as exception:
            print(f'{FATAL_TAG}: {exception}')
            self.close_drivers()

    def __threaded_sign_in(self):
        threads = []
        for driver in self.drivers:
            thread = threading.Thread(target=driver.start, args=(USERNAME, PASSWORD,
                                                                 self.webdriver_path, ))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()

    def run_tests_for(self, thread_id):
        ''' Runs test for the thread passed '''
        driver = self.drivers[thread_id]
        return _run_tests(driver, self.verbose)

    def close_drivers(self):
        ''' Close all drivers '''
        for driver in self.drivers:
            driver.close()


def _run_tests(driver, verbose):
    if verbose:
        print('{} Starting tests:'.format(INFO_TAG))
    test_result_bundle = TestResultBundle()
    errors = []
    tests = get_all_classes()
    for test in tests:
        instance = test(driver)
        if verbose:
            sys.stdout.write('\t- {}{}{}: '.format(Fore.CYAN,
                                                   instance.test_name, Fore.RESET))
            sys.stdout.flush()
        test_result = instance.run()
        if verbose:
            print(_color_test_result(test_result.test_result, test_result.test_message,
                                     test_result.elapsed))
        if not test_result.test_result:
            errors.append(test_result.test_message)
        test_result_bundle.add_test_result(test_result)
        driver.reset_to_base()
    return test_result_bundle


if __name__ == '__main__':
    pass


class WebDriverNotFoundException(Exception):
    ''' Exception raised when the webdriver is not found '''
    pass
