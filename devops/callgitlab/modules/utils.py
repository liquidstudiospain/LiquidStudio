''' Utils module '''
import datetime
import json
import re
import urllib.parse
import urllib.request
import urllib.error
import ssl

from colorama import init as colorama_init
from colorama import Fore

from models.exceptions import DeploymentIdFileNotFound

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

ENV_BUILD_URL = 'RUN_DISPLAY_URL'
ENV_BUILD_ID = 'BUILD_ID'
ENV_JOB_NAME = 'JOB_NAME'
ENV_LAST_COMMIT = 'gitlabMergeRequestLastCommit'
ENV_MR_IID = 'gitlabMergeRequestIid'
ENV_PROJECT_HTTP = 'gitlabTargetRepoHttpUrl'
ENV_PROJECT_ID = 'gitlabMergeRequestTargetProjectId'
ENV_TARGET_BRANCH = 'gitlabTargetBranch'
ENV_TOKEN = 'PRIVATE_TOKEN'
ENV_WORKSPACE = 'WORKSPACE'
ENV_USERNAME = 'gitlabMergedByUser'

MARKDOWN_BULLETS = ['+ ', '- ', '* ']
TEMPLATE_DESCRIPTION = ('Write here the test classes (separated with ' +
                        'spaces) to be run in the deploy or leave ' +
                        'empty if no test needed')


def get_repository_info(remote_url):
    ''' Gets the remote url bassed on the repository in the PWD '''
    if '@' in remote_url:
        ssh_regex = r'git@(.*):(.*)\/(.*)\.git'
        result = re.findall(ssh_regex, remote_url)
        if result and len(result) == 1:
            host, owner, project_name = result[0]
            host = f'http://{host}'
            return host, owner, project_name
        raise MalformedRemoteUrl('SSH', remote_url)
    else:
        http_regex = r'^(https?.*)\/(.*)\/(.*).git$'
        result = re.findall(http_regex, remote_url)
        if result and len(result) == 1:
            host, owner, project_name = result[0]
            return host, owner, project_name
        raise MalformedRemoteUrl('HTTP', remote_url)


def print_key_value_list(top_message, items):
    ''' Prints a key value list '''
    message = f'{top_message}'
    for key, value in items:
        message += f'\n{key_value_list(key, value)}'
    print(message)


def get_deployment_id(file_='deploy_id'):
    ''' Gets the deployment id from the file deployment_id '''
    try:
        with open(file_, 'r') as deployment_id_file:
            deployment_id = deployment_id_file.read()
        return deployment_id.strip()
    except FileNotFoundError:
        raise DeploymentIdFileNotFound(file_)


def get_current_date():
    ''' Returns a string with the current date in %y%m%d '''
    return datetime.datetime.now().strftime(r'%y%m%d-%H%m%S')
    # TODO check this


def key_value_list(key, value):
    ''' Returns a pretty formated list, with key in cyan '''
    return f'\t- {Fore.CYAN}{key}{Fore.RESET}: {value}'


def http_request(ssl_verify, url, headers, method, payload=None):
    ''' Utility method for doing http requests with urllib '''
    data = urllib.parse.urlencode(payload).encode("utf-8")

    request = urllib.request.Request(url=url, data=data,
                                     headers=headers, method=method)

    try:
        if ssl_verify:
            with urllib.request.urlopen(request) as response:
                response_status = response.status
                response_msg = response.msg
                response_reason = response.reason
                response_data = json.load(response)
        else:
            # Create context to avoid SSL verifications
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(request, context=ctx) as response:
                response_status = response.status
                response_msg = response.msg
                response_reason = response.reason
                response_data = json.load(response)

    except urllib.error.HTTPError as http_exception:
        response_status = http_exception.getcode()
        response_msg = http_exception.msg
        response_reason = http_exception.reason
        response_data = None  # TODO check how to do this
    return HTTPResponse(response_status, response_msg,
                        response_reason, response_data)


class HTTPResponse:
    ''' HTTP Response wrapper '''
    def __init__(self, status_code, message, reason, data):
        self.status_code = status_code
        self.message = message
        self.reason = reason
        self.data = data

    def __repr__(self):
        return (f'{Fore.RED}<HTTPResponse, {self.reason} '
                f'({self.status_code})>{Fore.RESET}')


class MalformedRemoteUrl(Exception):
    ''' Malformed Remote URL exception, launched in get_remote_url() '''
    def __init__(self, remote_type, remote_url):
        super().__init__(f'Remote \'{remote_url}\' interpreted as '
                         f'{remote_type} has invalid format')


class MalformedBuildUrl(Exception):
    ''' Malformed Remote URL exception, launched in get_remote_url() '''
    def __init__(self, build_url):
        super().__init__(f'Build Url \'{build_url}\' has invalid format')
