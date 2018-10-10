''' Test cases for Case Submit VisualForce Page '''
import sys
import inspect
import re

from seleniumrunner.tests import AbstractTest, TestResult
from utils import start_timer, stop_timer

PRESENT_IDS = [{"element_id": "title-page", "html_tag": "h1"},
               {"element_id": "input-name", "html_tag": "input"},
               {"element_id": "input-email", "html_tag": "input"},
               {"element_id": "input-problem", "html_tag": "textarea"},
               {"element_id": "button-submit", "html_tag": "input"}]

IDS_IN_TAGS = {"input": {'input-name', 'input-email', 'button-submit'},
               "textarea": {'input-problem'}}

HIDED_IDS = ['error-message']


def get_test_classes():
    ''' Returns all the Implemented Test Classes in this module '''
    return [name for name, obj in inspect.getmembers(sys.modules[__name__])
            if inspect.isclass(obj) and 'Abstract' not in name
            and name.endswith('Test')]


def get_all_classes():
    ''' Returns all the classes implemented '''
    return [CheckVisibleFieldsCaseSubmitTest, CreateNewCaseTest]


class CheckVisibleFieldsCaseSubmitTest(AbstractTest):
    ''' Test methods that check if certain tags are visible in a visualforcepage '''
    def __init__(self, driver):
        self.driver = driver
        self.url_to_component = self.driver.base_url + 'apex/VisualForcePage'
        self.errors = []
        self.test_name = self.__class__.__name__

    def run(self):
        time_start = start_timer()
        try:
            self.__run_test()
            assert not self.errors
            status = True
            message = 'Test finished correctly'
        except AssertionError as exception:
            self.errors.append(exception)
            status = False
            message = self.get_error_message()
        return TestResult(self.__class__.__name__, status, message, stop_timer(time_start))

    def get_error_message(self):
        return 'Couldnt find ids: ' + str(self.errors)

    def __run_test(self):
        self.driver.get(self.url_to_component)
        for element in PRESENT_IDS:
            try:
                self.driver.check_if_element_exists(element['html_tag'], element["element_id"])
            except AssertionError:
                self.errors.append(element["element_id"])


class CreateNewCaseTest(AbstractTest):
    ''' Creates a New Case '''
    def __init__(self, driver):
        self.driver = driver
        self.url_to_component = self.driver.base_url + 'apex/VisualForcePage'
        self.errors = []
        self.test_name = self.__class__.__name__

    def run(self):
        time_start = start_timer()
        try:
            self.__run_test()
            assert not self.errors
            status = True
            message = 'Test finished correctly'
        except AssertionError as exception:
            self.errors.append(exception)
            status = False
            message = self.get_error_message()
        return TestResult(self.__class__.__name__, status, message, stop_timer(time_start))


    def get_error_message(self):
        return f'Errors are {str(self.errors)}'

    def __run_test(self):
        self.driver.get(self.url_to_component)
        elements = self.__get_elements_by_tag_and_id()
        elements['input']['input-name'].send_keys('Error1')
        elements['input']['input-email'].send_keys('hola@gmail.com')
        elements['textarea']['input-problem'].send_keys('this is the problem')
        elements['input']['button-submit'].click()
        splitted_url = self.driver.current_url[8:].split('/')
        assert len(splitted_url) == 2 and len(splitted_url[1]) == 18, 'Case could not be created'

    def __get_elements_by_tag_and_id(self):
        elements = {}
        for tag in IDS_IN_TAGS:
            elements[tag] = {}
            for element in self.driver.get_elements_by_tag_and_id(tag, IDS_IN_TAGS[tag]):
                only_id = re.sub('.*:', '', element.get_attribute('id'))
                elements[tag][only_id] = element
        return elements
