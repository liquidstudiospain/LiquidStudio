''' Module to make different minnor calls to GitLab  '''
import json
import ssl
import sys
import urllib
import urllib.request
from urllib.error import HTTPError

from models.exceptions import UnknownGroups, UnknownUsername
from modules.utils import INFO_TAG, SUCCESS_LINE, SUCCESS_TAG, ERROR_TAG


def check_groups(host_url, token, group_name, username, ssl_verify):
    ''' Obtains if a user belongs to a group'''
    print(f'{INFO_TAG}Getting username ({username}) ID.')
    username_id = __get_username_id(host_url, token, username, ssl_verify)
    print(f'{SUCCESS_TAG}Found {username} ID : {username_id}.')
    print(f'{INFO_TAG}Getting groups ({group_name}) IDs.')
    groups_ids = __get_groups_ids(host_url, token, group_name, ssl_verify)
    print(f'{SUCCESS_TAG}Found {group_name} IDs : {groups_ids}.')

    for group_id in groups_ids:
        url = (f'{host_url}/api/v4/groups/{group_id}/members/{username_id}')
        group_match = set()
        try:
            response, response_body = call_gitlab(url, token,
                                                  'GET', ssl_verify)

        except HTTPError as exc:
            print(f'{ERROR_TAG}Error: {exc.code}. \n{ERROR_TAG}' +
                  f'We can´t find username: {username} on the following ' +
                  f'group: {group_id}.')
        else:
            group_match.add(group_id)
            print(f'{SUCCESS_LINE}Find username {username} in: {group_id} ' +
                  'group ID')
        if group_match:
            sys.exit(0)
        else:
            sys.exit(10)


def __get_username_id(host_url, token, username, ssl_verify):
    '''Gets the username ID'''
    url = (f'{host_url}/api/v4/users?username={username}')
    response, response_body = call_gitlab(url, token,
                                          'GET', ssl_verify)
    if response.status == 200 and response_body:
        return response_body[0]['id']
    else:
        raise UnknownUsername(username)


def __get_groups_ids(host_url, token, group_name, ssl_verify):
    '''Gets the group ID by the group name. '''
    group_ids = set()
    for group in group_name:
        url = (f'{host_url}/api/v4/groups?search={group}')
        response, response_body = call_gitlab(url, token,
                                              'GET', ssl_verify)
        if response.status == 200 and response_body:
            group_ids.add(response_body[0]['id'])
        else:
            pass
    if len(group_ids) == 0:
        raise UnknownGroups()
    return group_ids


def call_gitlab(url, token, http_method, ssl_verify):
    ''' Calls gitlab for adding or editing comments '''
    payload = {}
    data = urllib.parse.urlencode(payload).encode("utf-8")
    headers = {'Private-Token': token}
    request = urllib.request.Request(url=url, data=data,
                                     headers=headers, method=http_method)
    if ssl_verify:
        with urllib.request.urlopen(request) as response:
            response_body = json.load(response)
    else:
        # Create context to avoid SSL verifications
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(request, context=ctx) as response:
            response_body = json.load(response)

    return response, response_body
