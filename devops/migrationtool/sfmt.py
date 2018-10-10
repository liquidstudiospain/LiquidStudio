#!/usr/local/bin/python3
''' LS Migration Tool '''
import os
import platform
import sys
import time

from modules.list_metadata import run as run_list
from modules.utils import (CWD, ERROR_LINE, INFO_LINE, SFMT_HOME, SUCCESS_LINE,
                           print_logo)
from modules.utils.argparser import parse_args

__version__ = '1.5'


def main():
    ''' Main method '''
    args = parse_args()
    if args.option == 'version':
        print(__version__)
        sys.exit(0)
    print_logo()
    if args.option == 'package':
        __open_packages(args.packagexml)
    elif args.option in {'compare_meta', 'build_xml'}:
        run_list(args)
    elif args.option == 'about':
        __print_about()
    else:
        string_params = __get_string_param(vars(args).items())
        command = (f'ant -buildfile {SFMT_HOME}/configuration/build.xml '
                   f'-Dbasedir={CWD} {args.option} {string_params}')
        print(f'{INFO_LINE} {command}')
        error_code = os.system(command)
        if not error_code:
            print(f'{SUCCESS_LINE} {args.option.title()} was Successfull \a')
            message = f'say yeah! {args.option} was successfull'
        else:
            print(f'{ERROR_LINE} {args.option.title()} Failed \a')
            message = f'say oh no! {args.option} failed'
        __notify_process_end(message)


def __notify_process_end(message):
    ''' Notifies the end of the process by sound '''
    time.sleep(1)
    if platform.system() == 'Darwin':
        os.system(message)
    elif platform.system() == 'Windows':
        os.system('rundll32 user32.dll,MessageBeep -1')
    elif platform.system() == 'Linux':
        pass  # TODO Investigate how to notify


def __get_string_param(items):
    ''' Converts param to java like args '''
    return ''.join([f'-D{key}={value} ' for key, value in items
                    if key != 'option' and value is not None])


def __open_packages(package):
    ''' Open all the packages in the default editor, creating them if don't
        exists '''
    pre = 'destructiveChangesPre'
    post = 'destructiveChangesPost'
    if os.name == 'posix':  # Unix
        print(f'{INFO_LINE} Opening packages in default editor')
        os.system(f'touch {pre}.xml && '
                  f'open {pre}.xml')
        os.system(f'touch {package} && '
                  f'open {package}')
        os.system(f'touch {post}.xml && '
                  f'open {post}.xml')
    elif os.name == 'nt':  # Windows
        # TODO investigate how to create file if dont exists....
        # maybe initialize it with the default content??
        os.system(f'start configuration/{pre}.xml')
        os.system(f'start configuration/{package}')
        os.system(f'start configuration/{post}.xml')


def __print_about():
    ''' Prints about method '''
    print('Brought to you with ❤️ by m.nunez.diaz-montes')


if __name__ == '__main__':
    main()
