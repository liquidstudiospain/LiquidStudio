''' Utils module '''
import configparser
import glob
import itertools
import os

from colorama import Fore
from colorama import init as colorama_init
from pyfiglet import figlet_format

colorama_init(autoreset=True)

FILE_TAG = f'{Fore.YELLOW}[FILE]{Fore.RESET}'
DATA_TAG = f'{Fore.MAGENTA}[DATA]{Fore.RESET}'
INFO_TAG = f'{Fore.YELLOW}[INFO]{Fore.RESET}'
INFO_LINE = f'{Fore.YELLOW}[INFO]'
ERROR_TAG = f'{Fore.RED}[ERROR]{Fore.RESET}'
ERROR_LINE = f'{Fore.RED}[ERROR]'
SUCCESS_TAG = f'{Fore.GREEN}[SUCCESS]{Fore.RESET}'
SUCCESS_LINE = f'{Fore.GREEN}[SUCCESS]'
WARNING_TAG = f'{Fore.MAGENTA}[WARNING]{Fore.RESET}'
WARNING_LINE = f'{Fore.MAGENTA}[WARNING]'

TEST_LEVELS = ['NoTestRun', 'RunLocalTests', 'RunAllTestsInOrg']

FOLDERED_ITEMS = {'EmailTemplate', 'Dashboard', 'Document', 'Report'}

CREDENTIALS_HOME = os.environ.get('CREDENTIALS_HOME')
if not CREDENTIALS_HOME:
    print(f'{WARNING_TAG} CREDENTIALS_HOME environment variable not found, '
          f'using default path \'configuration/credentials\'')
    CREDENTIALS_HOME = 'configuration/credentials'


CWD = os.getcwd()
SFMT_HOME = os.getenv('SFMT_HOME')
if not SFMT_HOME:
    print(f'{WARNING_TAG} SFMT_HOME environment variable not found, using '
          f'default path \'configuration/credentials\'')
    SFMT_HOME = CWD


def print_logo():
    ''' Prints LS Logo in ASCII Art '''
    message = figlet_format('LS MigrationTool', font='big')
    print(f'{Fore.CYAN}{message}{Fore.RESET}')


def get_filename(environment, metadata_type, metadata_folder=None):
    ''' Generates the file name for the types passed '''
    metadata_folder_string = f'-{metadata_folder}' if metadata_folder else ''
    file_env_name = environment.replace('/', '_')
    return (f'list/list-{file_env_name}-{metadata_type}'
            f'{metadata_folder_string}.log')


def get_filenames(environment, metadata_type):
    ''' Returns all retrieved list files in list folder '''
    foldered = '*' if metadata_type in FOLDERED_ITEMS else None
    return glob.glob(get_filename(environment, metadata_type, foldered))


def get_key_value(key, value):
    ''' Returns a key value formated string '''
    return F'{Fore.CYAN}{key}{Fore.RESET}: \'{value}\''


def erase_file(file_path):
    ''' Erase the file passed '''
    try:
        os.remove(file_path) if os.path.exists(file_path) else None
    except PermissionError:
        print(f'{ERROR_TAG} Destination file \'{file_path}\' is in use, '
              f'please close it')
        response = input(
            f'{INFO_TAG} Enter [q] to end or close the file an enter ')
        if 'q' in response:
            exit(1)
        else:
            erase_file(file_path)


def get_credentials(source):
    ''' Extracts credentials from credentials file '''
    config_file_path = f'{CREDENTIALS_HOME}/{source}.properties'
    config = configparser.ConfigParser()
    with open(config_file_path) as lines:
        lines = itertools.chain(("[top]",), lines)  # This line does the trick.
        config.read_file(lines)
    username = config.get('top', 'username')
    password = config.get('top', 'password')
    serverurl = config.get('top', 'serverurl')
    token = config.get('top', 'token', fallback='')
    return username, password, token, 'test' in serverurl


class CompoundTokenDetectedException(Exception):
    """Base class for exceptions in this module."""
    pass


class EmptyTokenListException(Exception):
    """Base class for exceptions in this module."""
    pass
