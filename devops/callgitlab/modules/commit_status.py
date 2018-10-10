''' Update Commit Status Module '''
import json
import urllib
import ssl

from modules.utils import (ERROR_LINE, INFO_TAG, SUCCESS_LINE,
                           print_key_value_list)

STATUS = ['pending', 'running', 'success', 'failed', 'canceled']


def update_commit_status(host, token, project_id, commit, status,
                         build_url, project_name, ssl_verify):
    ''' Updates the commit status of the passed commit '''
    url = (f'{host}/api/v4/projects/{project_id}/statuses/{commit}')

    print_key_value_list(f'{INFO_TAG} Updating commit status:',
                         [('Host URL', host), ('Project ID', project_id),
                          ('Commmit SHA', commit), ('Status', status),
                          ('Build URL', build_url), ('Endpoint', url),
                          ('Project Name', project_name)])

    headers = {'Private-Token': token}

    payload = {'state': status, 'target_url': build_url,
               'name': project_name}

    data = urllib.parse.urlencode(payload).encode("utf-8")

    request = urllib.request.Request(url=url, data=data,
                                     headers=headers, method='POST')
    if ssl_verify:
        with urllib.request.urlopen(request) as response:
            json.load(response)
    else:
        # Create context to avoid SSL verifications
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(request, context=ctx) as response:
            json.load(response)

    if response.status == 201:
        print(f'{SUCCESS_LINE} Status of commit updated Successfully')
    else:
        raise Exception(f'{ERROR_LINE} Could not update commit status')
