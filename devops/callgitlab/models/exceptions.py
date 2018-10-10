''' Exception module '''


class CallGitabException(Exception):
    ''' Base Exception for filtering Call Gitlab Exceptions '''
    STATUS_CODE = 127


class InvalidProjectRef(CallGitabException):
    ''' Invalid project ref exception, launched when the passed refs for
        identifying the project aren't correct '''
    STATUS_CODE = 126


class DeploymentIdFileNotFound(CallGitabException):
    ''' Exception launched when the deployment id is not found '''
    STATUS_CODE = 125

    def __init__(self, file_):
        super().__init__(f'Deployment Id file \'{file_}\' not found')


class MergeRequestAlreadyMerged(CallGitabException):
    ''' Exception launched when the merge request trying to merge is already,
        merged '''
    STATUS_CODE = 124

    def __init__(self, merge_request_iid):
        super().__init__(f'Merge Request with iid \'{merge_request_iid}\' '
                         f'is already merged')


class NotEnoughPermissions(CallGitabException):
    ''' Exception launched when trying to call the api with
        not enough permissions '''
    STATUS_CODE = 123

    def __init__(self, name):
        super().__init__(f'API Call {name} Returned not enough permissions')


class DescriptionException(CallGitabException):
    ''' Exception throwed when a status different of 200 is launched when
        trying to retrieve a merge request description '''
    STATUS_CODE = 10

    def __init__(self, mr_iid):
        message = f'Cannot get description from MR: {mr_iid}'
        super().__init__(self, message)


class InvalidDescriptionFormat(CallGitabException):
    ''' Exception throwed when the Merge Request Description does not follow
        a valid format '''
    STATUS_CODE = 11

    def __init__(self):
        message = 'Merge Request Description does not match a valid format'
        super().__init__(self, message)


class TemplateDescription(CallGitabException):
    ''' Exception throwed when description is the same as the template '''
    STATUS_CODE = 177

    def __init__(self):
        message = ('Merge Request description is the same as the template.\n' +
                   'No test to launch.')
        super().__init__(self, message)


class UnknownUsername(CallGitabException):
    ''' Exception throwed when there arent any match with the username '''
    STATUS_CODE = 12

    def __init__(self, username):
        message = f'Unknown username {username}'
        super().__init__(self, message)


class UnknownGroups(CallGitabException):
    ''' Exception throwed when there arent any match with groups '''
    STATUS_CODE = 13

    def __init__(self):
        message = ('No results for the groups provided, please check the' +
                   ' spelling')
        super().__init__(self, message)
