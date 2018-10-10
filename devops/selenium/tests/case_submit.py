''' Test cases for Case Submit VisualForce Page '''
from tests import Test
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

PRESENT_IDS = [{"element_id": "title-page", "html_tag": "h1"},
               {"element_id": "input-name", "html_tag": "input"},
               {"element_id": "input-email", "html_tag": "input"},
               {"element_id": "input-problem", "html_tag": "textarea"},
               {"element_id": "button-submit", "html_tag": "input"}]
HIDED_IDS = ['error-message']


def get_all_classes():
    return [CheckVisibleFieldsCaseSubmitTest]

class CheckVisibleFieldsCaseSubmitTest(Test):
    def __init__(self, driver, url_base):
        self.driver = driver
        self.url_to_component = url_base + 'apex/VisualForcePage'
        self.errors = []
        self.test_name = self.__class__.__name__

    def run(self):
        try:
            self.__run_test()
            return True, 'OK'
        except AssertionError:
            return False, self.get_error_message()

    def get_error_message(self):
        return 'Couldnt find ids: ' + str(self.errors)

    def __run_test(self):
        self.driver.get(self.url_to_component)
        for element in PRESENT_IDS:
            self.__check_if_element_exists(element)
        assert not self.errors

    def __check_if_element_exists(self, element):
        try:
            ids = self.__get_ids_of_tag(element["html_tag"])
            assert self.__check_if_element_is_in(element["element_id"], ids)
        except AssertionError:
            self.errors.append(element["element_id"])


    def __get_ids_of_tag(self, tag):
        elements = self.driver.find_elements_by_tag_name(tag)
        return [element.get_attribute('id') for element in elements]

    def __check_if_element_is_in(self, element_id, elements_ids):
        return [element for element in elements_ids if element_id in element]
