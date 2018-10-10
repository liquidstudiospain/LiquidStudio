''' Module to comment of Merge Requests '''
import json
import re
import ssl
import sys
import urllib
import urllib.request

from models.exceptions import (DescriptionException, InvalidDescriptionFormat,
                               TemplateDescription)
from modules.utils import INFO_TAG, TEMPLATE_DESCRIPTION, print_key_value_list


def get_description(host_url, token, project_id, mr_iid, build_id, workspace,
                    ssl_verify):
    ''' Gets the description of a specific Merge Request defined
        by host, project and mr_iid '''
    url = (f'{host_url}/api/v4/projects/{project_id}/merge_requests/'
           f'{mr_iid}')
    print_key_value_list(f'{INFO_TAG} Adding new Comment to:',
                         [('MR IID', mr_iid), ('Project ID', project_id),
                          ('Host URL', host_url), ('Target Endpoint', url)])

    response, response_body = call_gitlab(url, token,
                                          'GET', ssl_verify)
    if response.status == 200:
        tests = __extract_tests(response_body['description'])
        save_tests_to_file(tests, build_id, workspace)
    else:
        raise DescriptionException(mr_iid)


def __extract_tests(description):
    ''' Extracts test string from a description merge request '''
    regex = r'\`\`\`\s+testsToBeRun\s+(.*)\s+\`\`\`'
    tests = re.findall(regex, description)
    if not tests or len(tests) > 1:
        raise InvalidDescriptionFormat()
    elif tests[0].strip() == TEMPLATE_DESCRIPTION:
        raise TemplateDescription()
    return tests[0].strip()


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


def save_tests_to_file(tests, build_id, workspace):
    ''' Saves message somewhere for future use '''
    with open(f'{workspace}/{build_id}-description.txt', 'w') as comment_file:
        comment_file.write(tests)
