''' Argparse module '''
import argparse
import os
import re

from modules.commit_status import STATUS
from modules.utils import (ENV_BUILD_ID, ENV_BUILD_URL, ENV_JOB_NAME,
                           ENV_LAST_COMMIT, ENV_MR_IID, ENV_PROJECT_HTTP,
                           ENV_PROJECT_ID, ENV_TARGET_BRANCH, ENV_TOKEN,
                           ENV_WORKSPACE, WARNING_TAG, ENV_USERNAME,
                           get_repository_info)


def parse_args():
    ''' Arg parser method, initializes the possible subparsers '''
    parser = argparse.ArgumentParser()

    # Global arguments
    subparsers = parser.add_subparsers(help='commands', dest='option')
    subparsers.required = True

    # Version
    subparsers.add_parser('version', help='Returns script version')

    # Create/Update Comment Subparser
    help_string = 'Creates or updates a comment into the passed mergerequest'
    comment_parser(subparsers.add_parser('comment', help=help_string))

    # Updates Commit Status Subparser
    help_string = 'Updates the build status of a commit'
    status_parser(subparsers.add_parser('status', help=help_string))

    # Updates Commit Status Subparser
    help_string = 'Accepts Merge Request, creates a Release Tag & Branch'
    release_parser(subparsers.add_parser('release', help=help_string))

    # Get MR description Subparser
    help_string = 'Gets the Merge Request Description.'
    description_parser(subparsers.add_parser('description', help=help_string))

    help_string = 'Obtains if a username belongs to a specific group.'
    check_group_parser(subparsers.add_parser('check-group', help=help_string))

    args = parser.parse_args()

    # Post Validations
    if args.option == 'comment':
        post_comment_parse_validation(args, parser)
        (args.host, args.project_name,
         args.project_owner) = get_repository_info(args.repo)

    if args.option == 'status':
        post_status_parse_validation(args, parser)
        (args.host, args.project_name,
         args.project_owner) = get_repository_info(args.repo)

    if args.option == 'description':
        description_parse_validation(args, parser)
        (args.host, args.project_name,
         args.project_owner) = get_repository_info(args.repo)

    if args.option == 'check-group':
        check_group_parse_validation(args, parser)
        (args.host, args.project_name,
         args.project_owner) = get_repository_info(args.repo)

    if args.option == 'release':
        post_release_parse_validation(args, parser)
        if 'release_branch' not in args or not args.release_branch:
            args.release_branch = f'V/{args.tag_name}'
        (args.host, args.project_owner,
         args.project_name) = get_repository_info(args.repo)

    if 'ssl_verify' in args and not args.ssl_verify:
        print(f'{WARNING_TAG} Not performing SSL verification')

    if 'host' in args and 'force_https' in args and args.force_https:
        old_host = args.host
        args.host = re.sub('^http://', 'https://', args.host)
        if old_host != args.host:
            print(f'{WARNING_TAG} Redirecting GitLab host from \'{old_host}\' '
                  f'to \'{args.host}\'')

    return args


def description_parse_validation(args, parser):
    '''Description Validation Errors '''
    missing_args = []
    if not args.merge_request_iid:
        missing_args.append((f'${ENV_MR_IID}', 'Merge Request Iid'))
    if not args.project_id:
        missing_args.append((f'${ENV_PROJECT_ID}', 'Project Id'))
    if not args.repo:
        missing_args.append((f'${ENV_PROJECT_HTTP}', 'Repository URL'))
    if not args.build_id:
        missing_args.append((f'${ENV_BUILD_ID}', 'Build Id'))
    if not args.workspace:
        missing_args.append((f'${ENV_WORKSPACE}', 'Workspace'))
    if not args.token:
        missing_args.append((f'${ENV_TOKEN}', 'Private Token'))
    if missing_args:
        missing_args_list = [f'{value} ({key})'
                             for key, value in missing_args]
        missing_args_str = '; '.join(missing_args_list)
        parser.error(f'Missing arguments not present as env variables: '
                     f'{missing_args_str}')


def check_group_parse_validation(args, parser):
    '''Check group Validation Errors '''
    missing_args = []
    if not args.repo:
        missing_args.append((f'${ENV_PROJECT_HTTP}', 'Repository URL'))
    if not args.token:
        missing_args.append((f'${ENV_TOKEN}', 'Private Token'))
    if not args.username:
        missing_args.append((f'${ENV_USERNAME}', 'Username'))
    if missing_args:
        missing_args_list = [f'{value} ({key})'
                             for key, value in missing_args]
        missing_args_str = '; '.join(missing_args_list)
        parser.error(f'Missing arguments not present as env variables: '
                     f'{missing_args_str}')


def post_comment_parse_validation(args, parser):
    ''' Post Comment Validation Errors '''
    missing_args = []
    if not args.merge_request_iid:
        missing_args.append((f'${ENV_MR_IID}', 'Merge Request Iid'))
    if not args.project_id:
        missing_args.append((f'${ENV_PROJECT_ID}', 'Project Id'))
    if not args.repo:
        missing_args.append((f'${ENV_PROJECT_HTTP}', 'Repository URL'))
    if not args.build_id:
        missing_args.append((f'${ENV_BUILD_ID}', 'Build Id'))
    if not args.workspace:
        missing_args.append((f'${ENV_WORKSPACE}', 'Workspace'))
    if not args.token:
        missing_args.append((f'${ENV_TOKEN}', 'Private Token'))
    if missing_args:
        missing_args_list = [f'{value} ({key})'
                             for key, value in missing_args]
        missing_args_str = '; '.join(missing_args_list)
        parser.error(f'Missing arguments not present as env variables: '
                     f'{missing_args_str}')


def post_status_parse_validation(args, parser):
    ''' Post Comment Validation Errors '''
    missing_args = []
    if not args.build_url:
        missing_args.append((f'${ENV_BUILD_URL}', 'Build URL'))
    if not args.repo:
        missing_args.append((f'${ENV_PROJECT_HTTP}', 'Repository URL'))
    if not args.token:
        missing_args.append((f'${ENV_TOKEN}', 'Private Token'))
    if not args.commit:
        missing_args.append((f'${ENV_LAST_COMMIT}', 'Last Commit Token'))
    if not args.job_name:
        missing_args.append((f'${ENV_JOB_NAME}', 'Job Name'))
    if missing_args:
        missing_args_list = [f'{value} ({key})'
                             for key, value in missing_args]
        missing_args_str = '; '.join(missing_args_list)
        parser.error(f'Missing arguments not present as env variables: '
                     f'{missing_args_str}')


def post_release_parse_validation(args, parser):
    ''' Post Comment Validation Errors '''
    missing_args = []
    if not args.target_branch:
        missing_args.append((f'${ENV_TARGET_BRANCH}', 'Target Branch'))
    if not args.repo:
        missing_args.append((f'${ENV_PROJECT_HTTP}', 'Repository URL'))
    if not args.token:
        missing_args.append((f'${ENV_TOKEN}', 'Private Token'))
    if not args.merge_request_iid:
        missing_args.append((f'${ENV_MR_IID}', 'Merge Request Iid'))
    if not args.project_id:
        missing_args.append((f'${ENV_PROJECT_ID}', 'Project Id'))
    if missing_args:
        missing_args_list = [f'{value} ({key})'
                             for key, value in missing_args]
        missing_args_str = '; '.join(missing_args_list)
        parser.error(f'Missing arguments not present as env variables: '
                     f'{missing_args_str}')


def description_parser(parser):
    '''Adds general credentials arguments to passed parser '''
    parser.add_argument('-mr', '--merge-request-iid',
                        default=os.environ.get(ENV_MR_IID),
                        help='Merge Request project identifier')
    parser.add_argument('-p', '--project-id',
                        default=os.environ.get(ENV_PROJECT_ID),
                        help='Project global identifier')
    parser.add_argument('-r', '--repo',
                        default=os.environ.get(ENV_PROJECT_HTTP),
                        help='Repository URL')
    parser.add_argument('-t', '--token',
                        default=os.environ.get(ENV_TOKEN),
                        help='Gitlab API Token (required)')
    parser.add_argument('-b', '--build-id',
                        default=os.environ.get(ENV_BUILD_ID),
                        help='Current build id')
    parser.add_argument('-w', '--workspace',
                        default=os.environ.get(ENV_WORKSPACE),
                        help='Workspace Path')
    parser.add_argument('-ns', '--no-ssl', action='store_false',
                        dest='ssl_verify',
                        help='Flag to verify the SSL in requests')
    parser.add_argument('-fh', '--force-https', action='store_true',
                        help='Flag to force https gitlab host')


def check_group_parser(parser):
    '''Adds general credentials arguments to passed parser '''
    parser.add_argument('-u', '--username',
                        default=os.environ.get(ENV_USERNAME),
                        help='Username to check inside groups')
    parser.add_argument('-r', '--repo',
                        default=os.environ.get(ENV_PROJECT_HTTP),
                        help='Repository URL')
    parser.add_argument('-t', '--token',
                        default=os.environ.get(ENV_TOKEN),
                        help='Gitlab API Token (required)')
    parser.add_argument('-g', '--groups', required=True, nargs='+',
                        help='Groups to check.')
    parser.add_argument('-ns', '--no-ssl', action='store_false',
                        dest='ssl_verify',
                        help='Flag to verify the SSL in requests')
    parser.add_argument('-fh', '--force-https', action='store_true',
                        help='Flag to force https gitlab host')


def comment_parser(parser):
    ''' Adds general credentials arguments to passed parser '''
    parser.add_argument('-b', '--build-id',
                        default=os.environ.get(ENV_BUILD_ID),
                        help='Current build id')
    parser.add_argument('-e', '--edit', action='store_true',
                        help='Launch in append instead of clear mode')
    parser.add_argument('-m', '--message', required=True, nargs='*',
                        help='Message content (edit = append to last message)')
    parser.add_argument('-mr', '--merge-request-iid',
                        default=os.environ.get(ENV_MR_IID),
                        help='Merge Request project identifier')
    parser.add_argument('-p', '--project-id',
                        default=os.environ.get(ENV_PROJECT_ID),
                        help='Project global identifier')
    parser.add_argument('-r', '--repo',
                        default=os.environ.get(ENV_PROJECT_HTTP),
                        help='Repository URL')
    parser.add_argument('-w', '--workspace',
                        default=os.environ.get(ENV_WORKSPACE),
                        help='Workspace Path')
    parser.add_argument('-t', '--token',
                        default=os.environ.get(ENV_TOKEN),
                        help='Gitlab API Token (required)')
    parser.add_argument('-ns', '--no-ssl', action='store_false',
                        dest='ssl_verify',
                        help='Flag to verify the SSL in requests')
    parser.add_argument('-fh', '--force-https', action='store_true',
                        help='Flag to force https gitlab host')


def status_parser(parser):
    ''' Adds validate notification arguments to passed parser '''
    parser.add_argument('-t', '--token',
                        default=os.environ.get(ENV_TOKEN),
                        help='Gitlab API Token')
    parser.add_argument('-p', '--project-id',
                        default=os.environ.get(ENV_PROJECT_ID),
                        help='Project global identifier')
    parser.add_argument('-r', '--repo',
                        default=os.environ.get(ENV_PROJECT_HTTP),
                        help='Repository URL')
    parser.add_argument('--status', '-s', choices=STATUS, required=True,
                        help='New build status of the commit')
    parser.add_argument('--commit', '-c',
                        default=os.environ.get(ENV_LAST_COMMIT),
                        help='Commit to update')
    parser.add_argument('--build_url', '-b',
                        default=os.environ.get(ENV_BUILD_URL),
                        help='Commit to update')
    parser.add_argument('--job-name', '-j',
                        default=os.environ.get(ENV_JOB_NAME),
                        help='Job Name')
    parser.add_argument('-ns', '--no-ssl', action='store_false',
                        dest='ssl_verify',
                        help='Flag to verify the SSL in requests')
    parser.add_argument('-fh', '--force-https', action='store_true',
                        help='Flag to force https gitlab host')


def release_parser(parser):
    ''' Parser for release option '''
    parser.add_argument('-p', '--project-id',
                        default=os.environ.get(ENV_PROJECT_ID),
                        help='Project global identifier')
    parser.add_argument('-r', '--repo',
                        default=os.environ.get(ENV_PROJECT_HTTP),
                        help='Repository URL')
    parser.add_argument('-to', '--token',
                        default=os.environ.get(ENV_TOKEN),
                        help='Gitlab API Token (required)')
    parser.add_argument('-mr', '--merge-request-iid',
                        default=os.environ.get(ENV_MR_IID),
                        help='Merge Request project identifier')
    parser.add_argument('-t', '--target-branch',
                        default=os.environ.get(ENV_TARGET_BRANCH),
                        help='Merge Request Target Branch')
    parser.add_argument('-tn', '--tag_name', required=True,
                        help='Name for creating the tag and branch')
    rb_help = 'Name for the release branch, default=V/{tag_name}'
    parser.add_argument('-rb', '--release_branch', help=rb_help)
    parser.add_argument('-m', '--message', help='Tag Message')
    parser.add_argument('-rd', '--release_description',
                        help='Tag Release Description')
    parser.add_argument('-ns', '--no-ssl', action='store_false',
                        dest='ssl_verify',
                        help='Flag to verify the SSL in requests')
    parser.add_argument('-fh', '--force-https', action='store_true',
                        help='Flag to force https gitlab host')
