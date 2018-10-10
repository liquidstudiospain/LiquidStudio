''' Call Gitlab Method '''
import sys

from models.exceptions import CallGitabException
from modules.custom_argparser import parse_args
from modules.commit_status import update_commit_status
from modules.mergerequest_description import get_description
from modules.mergerequest_comment import add_comment, edit_comment
from modules.create_release import create_release
from modules.misc_gitlab_calls import check_groups
from modules.utils import ERROR_LINE

__version__ = '1.4.2'


def handle_options(args):
    ''' Switcher for different options '''
    if args.option == 'version':
        print(__version__)
        sys.exit(0)
    elif args.option == 'comment':
        if args.edit:
            edit_comment(args.host, args.token, args.project_id,
                         args.merge_request_iid, args.message,
                         args.build_id, args.workspace, args.ssl_verify)
        else:
            add_comment(args.host, args.token, args.project_id,
                        args.merge_request_iid, args.message,
                        args.build_id, args.workspace, args.ssl_verify)
    elif args.option == 'status':
        update_commit_status(args.host, args.token, args.project_id,
                             args.commit, args.status, args.build_url,
                             args.job_name, args.ssl_verify)
    elif args.option == 'release':
        create_release(args.host, args.token, args.project_id,
                       args.merge_request_iid, args.tag_name,
                       args.target_branch, args.message,
                       args.release_description, args.release_branch,
                       args.ssl_verify)
    elif args.option == 'description':
        get_description(args.host, args.token, args.project_id,
                        args.merge_request_iid, args.build_id,
                        args.workspace, args.ssl_verify)
    elif args.option == 'check-group':
        check_groups(args.host, args.token, args.groups, args.username,
                     args.ssl_verify)


def main():
    ''' Main Method '''
    try:
        args = parse_args()
        handle_options(args)
    except CallGitabException as gitlab_exception:
        print(f'{ERROR_LINE} {gitlab_exception}')
        sys.exit(gitlab_exception.STATUS_CODE)


if __name__ == '__main__':
    main()
