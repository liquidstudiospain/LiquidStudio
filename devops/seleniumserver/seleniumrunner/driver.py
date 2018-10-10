''' WebDriver Implementation '''
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from utils import Status, INFO_TAG, THREAD_TAG, FATAL_TAG


class Driver(webdriver.Chrome):
    ''' WebDriver implementation extends from chrome '''
    def __init__(self, base_url, thread_id=None):
        if thread_id == -1: # never do this
            super(Driver, self).__init__('')
        self.thread_id = thread_id
        self.status = Status.CREATED
        self.base_url = base_url

    def start(self, username, password, path_webdriver):
        ''' Starts driver and sign in to Salesforce '''
        super(Driver, self).__init__(path_webdriver, chrome_options=Driver.__get_options())
        self.__login(username, password)
        print(f'{INFO_TAG} Thread-{self.thread_id} signed in succesfully')
        self.status = Status.WAITING

    def close(self):
        if self.status != Status.CLOSED:
            super(Driver, self).close()
            self.status = Status.CLOSED

    @staticmethod
    def __get_options():
        options = Options()
        options.add_argument('--disable-web-security')
        options.add_argument('--user-data-dir')
        options.add_argument('--disable-application-cache')
        options.add_argument('--media-cache-size=1')
        options.add_argument('--disk-cache-size=1')
        if not os.name == 'nt':
            print(f'{INFO_TAG} Running ChromeDriver in headless mode')
            options.add_argument('--headless')
        # options.add_argument('--disable-gpu')

    def __mul__(self, number_of_items):
        return [Driver(self.base_url, thread_id=i) for i in range(number_of_items)]

    def __rmul__(self, number_of_items):
        return [Driver(self.base_url, thread_id=i) for i in range(number_of_items)]

    def __repr__(self):
        return f'<Driver({self.thread_id}), {self.status.name}>'

    def __str__(self):
        return f'{THREAD_TAG} {self.thread_id} {self.base_url} ({self.status.name})'

    def reset_to_base(self):
        ''' Resets to base URL '''
        self.get(self.base_url)

    def set_base_url(self, base_url):
        ''' Resets base url '''
        self.base_url = base_url
        self.reset_to_base()

    def __login(self, username, password):
        ''' Logs in to passed to passed environment, with passed username and password '''
        try:
            if self.base_url != self.current_url:
                self.get(self.base_url)
            assert "Salesforce" in self.title
            self.find_element_by_id("username").send_keys(username)
            self.find_element_by_id("password").send_keys(password)
            self.find_element_by_id("Login").click()
            WebDriverWait(self, 1)
            self.get(self.base_url)
            WebDriverWait(self, 10).until(
                EC.presence_of_element_located((By.ID, 'phHeaderLogoImage')))
            return True
        except Exception as exception:
            print(f'{FATAL_TAG} {exception}')
            print(f'{FATAL_TAG} Could not sign in, aborting')

    def get_element_by_tag_and_id(self, tag, id_):
        ''' Returns the element for the tag and id passed '''
        elements = self.find_elements_by_tag_name(tag)
        element = [element for element in elements
                   if id_ in element.get_attribute('id')]
        if len(element) > 1:
            raise IdNotUniqueException(f'More than one element with tag {tag} and id {id} found')
        return element[0]

    def get_elements_by_tag_and_id(self, tag, ids):
        ''' Returns a list of elements for the tag and ids passed '''
        elements = self.find_elements_by_tag_name(tag)
        return [element for element in elements
                if _has_substring(element.get_attribute('id'), ids)]

    def get_ids_of_tag(self, tag):
        ''' Returns all the ids of a specified tag '''
        return [element.get_property('id') for element in self.find_elements_by_tag_name(tag)
                if element.get_property('id') is not '']

    def check_if_element_exists(self, element_tag, element_id):
        ''' Raise exception if cannot find a tag with the id passed '''
        ids = self.get_ids_of_tag(element_tag)
        for id_ in ids:
            if element_id in id_:
                return
        assert False

    def get_local(self, path):
        ''' Navigate to the passed path '''
        self.get(f'{self.base_url}/{path}')


def _has_substring(element_id, ids):
    ''' Workaround for not having a method to detect  '''
    for id_ in ids:
        if id_ in element_id:
            return True


class IdNotUniqueException(Exception):
    ''' Tryed to search for one Id but detected more '''
    pass
