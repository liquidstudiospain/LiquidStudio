''' Auxiliar Variables, classes and methods '''
import os
import time
import random

from enum import Enum
from colorama import Fore
from flask import jsonify

SUCCESS_TAG = '{}[SUCCESS]{}'.format(Fore.GREEN, Fore.RESET)
ERROR_TAG = '{}[ERROR]{}'.format(Fore.RED, Fore.RESET)
INFO_TAG = f'{Fore.YELLOW}[INFO]{Fore.RESET}'
THREAD_TAG = f'{Fore.YELLOW}[THREAD]{Fore.RESET}'
FATAL_TAG = f'{Fore.RED}[FATAL]{Fore.RESET}'
PATH_WEBDRIVER = ('C:\\devops\\chromedriver.exe'
                  if os.name == 'nt' else '/usr/local/bin/chromedriver')


def _clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def _color_test_result(status, message, elapsed):
    color = Fore.GREEN if status else Fore.RED
    return '{}{}{}'.format(color, f'{message} in {elapsed} ms', Fore.RESET)


def serialize_response(code, status, description, payload=None):
    ''' Generate serialized responses '''
    response = {'code': code, 'status': status, 'description': description}
    if payload:
        response['payload'] = payload
    return jsonify(response)


class Status(Enum):
    ''' Possible Status of the WebDriver '''
    WAITING = 0
    RUNNING = 1
    FINISHED = 2
    ERROR = -1
    CLOSED = -2
    LOGGEDIN = 4
    CREATED = 5


def start_timer():
    ''' Returns the time in ns '''
    return __get_time_in_ms()


def stop_timer(time_start, description=None):
    ''' Calculates the elapsed time between the actual time and the passed time,
    prints the information, and returns the elapsed time '''
    time_stop = __get_time_in_ms()
    elapsed = round(time_stop - time_start, 2)
    if description:
        print(f'{INFO_TAG} {elapsed} ns in {description}')
    return elapsed


def __get_time_in_ms():
    return time.time() * pow(10, 3)


def get_random_color(string):
    random_color = random.choice([Fore.YELLOW, Fore.CYAN, Fore.GREEN,
                                  Fore.MAGENTA, Fore.RED, Fore.WHITE])
    return f'{random_color}{string}{Fore.RESET}'


def get_lines():
    file_name = 'list.log'
    if os.path.exists(file_name):
        file = open(file_name, 'r')
        file_str = file.read()
        return file_str.split('\n')
    return []
