''' Module to comment of Merge Requests '''
import json
import urllib
import urllib.request
import ssl

from modules.utils import (ERROR_LINE, INFO_TAG, MARKDOWN_BULLETS,
                           SUCCESS_LINE, print_key_value_list)


def add_comment(host_url, token, project_id, mr_iid, new_comments,
                build_id, workspace, ssl_verify):
    ''' Adds a new comment with the message passed
        to the the merge request defined by host, project and mr_iid '''
    url = (f'{host_url}/api/v4/projects/{project_id}/merge_requests/'
           f'{mr_iid}/notes')

    print_key_value_list(f'{INFO_TAG} Adding new Comment to:',
                         [('Comment', new_comments), ('MR IID', mr_iid),
                          ('Project ID', project_id), ('Host URL', host_url),
                          ('Target Endpoint', url)])

    comment_body = append_new_comments(new_comments)

    response, response_body = call_gitlab(url, comment_body, token,
                                          'POST', ssl_verify)

    if response.status == 201:
        comment_id = str(response_body['id'])
        save_comment_to_file(comment_body, build_id, comment_id, workspace)
        print(f'{SUCCESS_LINE} Comment created succesfully with id '
              f'\'{comment_id}\', saved to ./{build_id}-comment.txt')
    else:
        raise Exception(f'{ERROR_LINE} Could not create comment on merge '
                        f'request ({response_body} -- {response.status})')


def edit_comment(host_url, token, project_id, mr_iid,
                 new_comments, build_id, workspace, ssl_verify):
    ''' Edits existing comment appending the message passed
        in the the merge request defined by host, project and mr_iid '''
    comment_id, last_comments = get_last_comment(workspace, build_id)

    url = (f'{host_url}/api/v4/projects/{project_id}/merge_requests/'
           f'{mr_iid}/notes/{comment_id}')

    print_key_value_list(f'{INFO_TAG} Editing Comment with:',
                         [('Comment', new_comments), ('MR IID', mr_iid),
                          ('Project ID', project_id), ('Host URL', host_url),
                          ('Target Endpoint', url)])

    comment_body = append_new_comments(new_comments, last_comments)

    save_comment_to_file(comment_body, build_id, comment_id, workspace)

    response, _ = call_gitlab(url, comment_body, token, 'PUT', ssl_verify)

    if response.status != 200:
        raise Exception(f'{ERROR_LINE} Could not create comment on merge '
                        f'request (={response.status})')
    else:
        print(f'{SUCCESS_LINE} Comment updated succesfully')


def call_gitlab(url, comment_body, token, http_method, ssl_verify):
    ''' Calls gitlab for adding or editing comments '''
    payload = {'body': comment_body}
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


def get_last_comment(workspace, build_id):
    ''' Returns  '''
    with open(f'{workspace}/{build_id}-comment.txt', 'r+') as message_file:
        comment = message_file.read().splitlines()
        comment_id = comment.pop(0).strip()

    return comment_id, comment


def append_new_comments(new_comments, comments_history=[]):
    ''' Returns the body of the comment after appending new messages '''
    for comment in new_comments:
        if __requires_blank_line(comment, comments_history):
            comments_history.append('')

        comments_history.append(comment.rstrip())
    return '\n'.join(comments_history)


def save_comment_to_file(comment, build_id, comment_id, workspace):
    ''' Saves message somewhere for future use '''
    with open(f'{workspace}/{build_id}-comment.txt', 'w') as comment_file:
        comment_file.write(f'{comment_id}\n')
        comment_file.write(f'{comment}\n')


def __requires_blank_line(comment, comments_history):
    ''' Returns, based on the previous commit, if it's necessary to write a
        new blank line in order to separate content due to MD formatting '''
    if not comments_history:
        return False
    elif (comment.strip()[:2] in MARKDOWN_BULLETS and
          comments_history[-1].strip()[:2] in MARKDOWN_BULLETS):
        return False  # if new comment and last comment are bullets
    return True
