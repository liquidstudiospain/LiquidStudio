''' Models module for git related objects '''
from models.exceptions import CallGitabException
from modules.utils import (INFO_TAG, ERROR_LINE, WARNING_LINE, http_request,
                           print_key_value_list)


class GitObject:
    ''' Abstract method for git object '''
    def create_local(self):
        ''' Creates object in the local repository '''
        raise NotImplementedError()

    def create_remote(self, remote, project, ssl_verify):
        ''' Creates object in the remote repository '''
        raise NotImplementedError()


class Branch(GitObject):
    ''' Model for git Branches '''
    def __init__(self, branch, ref):
        self.branch = branch
        self.ref = ref

    def create_local(self):
        raise NotImplementedError()

    def create_remote(self, remote, project, ssl_verify):
        url = (f'{remote.url}/api/v4/projects/{project.ref}'
               f'/repository/branches')
        headers = {'Private-Token': remote.token}
        payload = {
            'branch': self.branch,
            'ref': self.ref
        }
        method = 'POST'

        print_key_value_list(f'{INFO_TAG} Creating branch:',
                             [('Remote URL', remote.url),
                              ('Project REF', project.ref),
                              ('Branch Name', self.branch),
                              ('Source Ref', self.ref),
                              ('Endpoint', f'({method}) {url}')])
        response = http_request(ssl_verify, url, headers, method, payload)

        if response.status_code == 201:
            print(f'{INFO_TAG} Branch \'{self.branch}\' created')


class Tag(GitObject):
    ''' Model for git Tags '''
    def __init__(self, tag_name, ref, message=None, release_description=None):
        self.tag_name = tag_name
        self.ref = ref
        self.message = message
        self.release_description = release_description

    def create_local(self):
        raise NotImplementedError()

    def create_remote(self, remote, project, ssl_verify):
        url = (f'{remote.url}/api/v4/projects/{project.ref}'
               f'/repository/tags')
        headers = {'Private-Token': remote.token}
        payload = {'tag_name': self.tag_name, 'ref': self.ref}
        if self.message:
            payload['message'] = self.message
        if self.release_description:
            payload['release_description'] = self.release_description

        method = 'POST'

        print_key_value_list(f'{INFO_TAG} Creating tag with:',
                             [('Remote URL', remote.url),
                              ('Project REF', project.ref),
                              ('Tag Name', self.tag_name),
                              ('Ref', self.ref), ('Message', self.message),
                              ('Description', self.release_description),
                              ('Endpoint', f'({method}) {url}')])
        response = http_request(ssl_verify, url, headers, method, payload)

        if response.status_code == 201:
            print(f'{INFO_TAG} Tag Created')
        else:
            raise Exception(response)


class MergeRequest(GitObject):
    ''' Model for git Merge Requests '''
    def __init__(self, iid):
        self.iid = iid

    def create_local(self):
        raise NotImplementedError('Merge Requests are remote only')

    def create_remote(self, remote, project, ssl_verify):
        raise NotImplementedError()

    def accept_merge_request(self, remote, project, ssl_verify):
        ''' Accepts the merge request on passed remote/project '''
        url = (f'{remote.url}/api/v4/projects/{project.ref}'
               f'/merge_requests/{self.iid}/merge')
        headers = {'Private-Token': remote.token}
        payload = {}
        method = 'PUT'

        print_key_value_list(f'{INFO_TAG} Accepting Merge Request:',
                             [('Remote URL', remote.url),
                              ('Project REF', project.ref),
                              ('MR IID', self.iid),
                              ('Endpoint', f'({method}) {url}')])
        response = http_request(ssl_verify, url, headers, method, payload)

        if response.status_code == 200:
            print(f'{INFO_TAG} Merge Request Accepted')
        elif response.status_code == 405:
            print(f'{WARNING_LINE} Merge Request Already accepted')
        else:
            print(f'{ERROR_LINE} Unhandled Error {response}')
            raise CallGitabException(response)
            # raise MergeRequestAlreadyMerged(self.iid)


class Project(GitObject):
    ''' Project Model (repository in local git) '''
    def __init__(self, project_id):
        self.id_ = project_id
        self.ref = project_id

    def create_local(self):
        raise NotImplementedError()

    def create_remote(self, remote, project, ssl_verify):
        raise NotImplementedError()


class Remote:
    ''' Remote model object '''
    def __init__(self, url, token):
        self.url = url
        self.token = token
