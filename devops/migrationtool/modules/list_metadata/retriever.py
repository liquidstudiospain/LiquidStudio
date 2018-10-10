''' Retrieves Metadata from Salesforce '''
import copy
import os
import re
import threading
from queue import Queue

from simple_salesforce import Salesforce

from modules.utils import (ERROR_TAG, FOLDERED_ITEMS, INFO_TAG, SUCCESS_TAG,
                           WARNING_TAG, erase_file, get_credentials,
                           get_filename)

WARNING_QUEUE = Queue()
ERROR_QUEUE = Queue()


def retrieve_metadata(sources, metadata_types, verbose, local):
    ''' Retrieves the metadata passed from the environment passed '''
    all_folders_info = []
    if not metadata_types:
        metadata_types = __get_metadata_types(sources, verbose, local)
    if not local:
        print(f'{INFO_TAG} Retrieving {metadata_types} from {sources}')
        for metadata_type in metadata_types:
            if metadata_type in FOLDERED_ITEMS:
                print(f'{INFO_TAG} Detected Foldered Item \'{metadata_type}\'')
                if not all_folders_info:
                    all_folders_info = __retrieve_folders(sources)
                __threaded_retrieve(sources, metadata_type, verbose,
                                    all_folders_info[metadata_type])
            else:
                __threaded_retrieve(sources, metadata_type, verbose)
    return metadata_types


def __get_metadata_types(source, verbose, local):
    ''' Describe all the metadata available for the passed source '''
    if not local:
        print(f'{INFO_TAG} Retrieving available metadata types from {source}')
        os.chdir('configuration')
        command = f'ant describeMetadata -Dsource={source}'
        if not verbose:
            command = f'{command} >{os.devnull} 2>&1'
        if os.system(command):
            print(f'{ERROR_TAG} Error at retrieving types from \'{source}\'')
        else:
            print(f'{SUCCESS_TAG} All metadata types '
                  f'retrieved from \'{source}\'')
        os.chdir('..')
    data = open('describe.log', 'r').read()
    return set(re.findall('(?m)(?<=\\bXMLName: ).*$', data))


def __threaded_retrieve(sources, metadata_type, verbose, folders=None):
    threads = []
    os.chdir('configuration')
    for source in sources:
        thread = threading.Thread(
            target=__list_metadata, args=(source, metadata_type, verbose, ),
            kwargs={'folders': folders[source] if folders else None})
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    while not ERROR_QUEUE.empty():
        retrieve_info = ERROR_QUEUE.get()
        __list_metadata(retrieve_info['source'],
                        retrieve_info['metadata_type'], verbose,
                        counter=retrieve_info['counter'])
    os.chdir('..')


def __list_metadata(source, metadata_type, verbose, counter=0,
                    folder=None, folders=None):
    if folders:
        for folder in folders:
            __list_metadata(source, metadata_type, verbose,
                            counter=0, folder=folder)
        return
    folder_ant_string = f'-Dmetadata_folder={folder}' if folder else ''
    folder_log_string = f'-{folder}' if folder else ''
    command = (f'ant listMetadata -Dsource={source} -Dtype={metadata_type} '
               f'{folder_ant_string}')
    file_name = get_filename(source, metadata_type, folder)
    erase_file(f'../{file_name}')
    if not verbose:
        command = f'{command} >{os.devnull} 2>&1'
    if os.system(command):
        print(f'{ERROR_TAG} Error at retrieving \'{metadata_type}'
              f'{folder_log_string}\' from \'{source}\'')
        counter = counter + 1
        if counter == 4:
            print(f'{WARNING_TAG} Maximum number of retries archived, erasing '
                  f'type \'{metadata_type}{folder_log_string}\' '
                  f'from \'{source}\'')
            WARNING_QUEUE.put(metadata_type)
        else:
            ERROR_QUEUE.put({"metadata_type": metadata_type,
                             "source": source,
                             "counter": counter,
                             "folder": folder})
    else:
        if os.path.exists(f'../{file_name}'):
            print(f'{SUCCESS_TAG} \'{metadata_type}{folder_log_string}\' '
                  f'metadata retrieved from \'{source}\'')
        else:
            print(f'{WARNING_TAG} No metadata avalailable for '
                  f'\'{metadata_type}{folder_log_string}\' in '
                  f'\'{source}\' at \'{file_name}\'')
            WARNING_QUEUE.put(metadata_type)


def __retrieve_folders(sources):
    all_folders = {}
    for source in sources:
        username, password, token, is_sandbox = get_credentials(source)
        salesforce_session = Salesforce(username, password, token,
                                        sandbox=is_sandbox)
        folder_data = salesforce_session.query('SELECT DeveloperName, Type '
                                               'FROM Folder')
        for metadata_type in FOLDERED_ITEMS:
            new_item = copy.copy(folder_data['records'][0])
            new_item['DeveloperName'] = ''
            new_item['Type'] = metadata_type
            folder_data['records'].append(new_item)
        all_folders = __generate_folder_dict(folder_data, source, all_folders)
    return all_folders


def __generate_folder_dict(folders_data, source, all_folders):
    for folder_data in folders_data['records']:
        meta_type = ('EmailTemplate' if folder_data['Type'] == 'Email'
                     else folder_data['Type'])
        meta_developer_name = folder_data['DeveloperName']
        if meta_type and meta_developer_name:
            if meta_type not in all_folders:
                all_folders[meta_type] = {}
            if source not in all_folders[meta_type]:
                all_folders[meta_type][source] = set()
            all_folders[meta_type][source].add(meta_developer_name)
    return all_folders
