''' Argparser module '''
import argparse
import os

from modules.list_metadata import generate_parser as list_generate_parser
from modules.utils import SFMT_HOME, TEST_LEVELS, WARNING_LINE


def parse_args():
    ''' Parses args '''
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='commands', dest='option')
    subparsers.required = True

    version_help = 'Returns sfmt version'
    subparsers.add_parser('version', help=version_help)

    retrieve_help = 'Retrieves metadata from a package.xml or a named package'
    retrieve_parser = subparsers.add_parser('retrieve', help=retrieve_help)
    __add_retrieve_options(retrieve_parser, default_folder='retrieve')

    post_parser = subparsers.add_parser('post', help='Posts Metadata')
    __add_post_options(post_parser)

    r_a_p_help = 'Retrieves and Posts Metadata'
    r_a_p_parser = subparsers.add_parser('retrieveAndPost', help=r_a_p_help)
    __add_retrieve_and_post_options(r_a_p_parser)

    test_parser = subparsers.add_parser('test', help='Launches Tests')
    test_parser.add_argument('-t', '--target', required=True,
                             help='Destination environment')
    __add_test_option(test_parser)

    package_help = 'Opens metadata XMLs'
    __add_package_option(subparsers.add_parser('package', help=package_help))

    differ_help = 'Gets the diff of two environments'
    differ_parser = subparsers.add_parser('differ', help=differ_help)
    __add_differ_options(differ_parser)

    describe_help = 'Gets the metadata available for the passed environment'
    __add_describe_options(subparsers.add_parser('describe',
                                                 help=describe_help))

    compare_meta_help = 'Compares specified metadata from passed environments'
    compare_meta_parser = subparsers.add_parser('compare_meta',
                                                help=compare_meta_help)
    list_generate_parser(compare_meta_parser, is_build_xml=False)

    build_xml_help = 'Generates package.xml from all the elements of an org'
    build_xml_parser = subparsers.add_parser('build_xml',
                                             help=build_xml_help)
    list_generate_parser(build_xml_parser, is_build_xml=True)

    subparsers.add_parser('about', help='Prints about info')

    args = parser.parse_args()

    if 'packagenames' in args and args.packagenames and 'packagexml' in args:
        args.packagexml = None

    if 'folder' in args and args.folder == 'backup':
        parser.error('Folder can\'t be backup, or you will '
                     'delete all your backups...')

    if 'packagexml' in args:
        packagexml = args.packagexml
        if not os.path.isfile(packagexml):
            default_package = f'{SFMT_HOME}/configuration/package.xml'
            print(f'{WARNING_LINE} No package found in current directory, '
                  f'trying in default path \'{default_package}\'')
            if not os.path.isfile(default_package):
                workspace_package = 'configuration/package.xml'
                print(f'{WARNING_LINE} No package found in default directory, '
                      f'trying in workspace  \'{workspace_package}\'')
                default_package = f'./configuration/package.xml'
                if not os.path.isfile(workspace_package):
                    parser.error(f'{packagexml} could not be found...')
                else:
                    args.packagexml = workspace_package
            else:
                args.packagexml = default_package

    if 'build_xml' in args.option:
        print(args)
        if len(args.sources) > 1:
            parser.error('build_xml option only accepts one source')
    return args


def __add_describe_options(parser):
    ''' Describe options helper method '''
    parser.add_argument('-s', '--source', required=True,
                        help='Source environment')
    result_file_help = 'Specifies the result file, default=result_file'
    parser.add_argument('-r', '--result-file', default='describe.log',
                        help=result_file_help)


def __add_retrieve_and_post_options(parser):
    ''' Retrieve and Post options helper method '''
    retry_help = 'Retries last RetrieveAndPost omiting the retrieve'
    parser.add_argument('-r', '--retry', action='store_true', help=retry_help)
    pause_help = 'Paused until unser input between the retrieve and the post'
    parser.add_argument('-pa', '--pause', action='store_true', help=pause_help)
    __add_retrieve_options(parser, default_folder='retrieveAnd')
    __add_post_options(parser, r_a_p=True)


def __add_differ_options(parser):
    ''' Differ options helper method '''
    __add_retrieve_options(parser, default_folder='differ')
    parser.add_argument('-t', '--target', required=True,
                        help='Destination environment')


def __add_retrieve_options(parser, default_folder):
    ''' Retrieve options helper method '''
    __add_package_option(parser)
    parser.add_argument('-s', '--source', required=True,
                        help='Source environment')
    parser.add_argument('-f', '--folder', default=default_folder,
                        help='Folder to save the metadata retrieved')


def __add_post_options(parser, r_a_p=False):
    ''' Post options helper methods '''
    parser.add_argument('-pre', '--predestructive', action='store_true',
                        help='Flag to copy or not the predestructive file')
    parser.add_argument('-post', '--postdestructive', action='store_true',
                        help='Flag to copy or not the postdestructive file')
    parser.add_argument('-d', '--deploy', const='Deploy', dest='post_type',
                        action='store_const', default='Validate',
                        help='Flag to activate Deploy instead of Validate')
    __add_test_option(parser)
    parser.add_argument('-t', '--target', required=True,
                        help='Destination environment')
    if not r_a_p:
        parser.add_argument('-f', '--folder', default='post',
                            help='Post folder')


def __add_package_option(parser):
    ''' Package options helper method '''
    # more package logic at the end of the parser
    xor_parser = parser.add_mutually_exclusive_group()
    xor_parser.add_argument('-pn', '--packagenames',
                            help='Name of the package in configuration folder')
    xor_parser.add_argument('-p', '--packagexml', default=f'package.xml',
                            help='Name of the package in configuration folder')
    xor_parser.add_argument('-a', '--all', const='packageAll.xml',
                            action='store_const', dest='packagexml',
                            help='Retrieves all metadata')


def __add_test_option(parser):
    ''' Test options helper method '''
    xor_parser = parser.add_mutually_exclusive_group()
    xor_parser.add_argument('-tl', '--test-level', choices=TEST_LEVELS,
                            default='RunLocalTests',
                            help='Specifies the Test Level to run')
    xor_parser.add_argument('-nt', '--no-test', dest='test_level',
                            const='NoTestRun',
                            help='Donnot run tests', action='store_const')
