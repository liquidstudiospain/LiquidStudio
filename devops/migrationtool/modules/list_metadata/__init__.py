''' Retrieves the list of metadata for the passed
    types and source environments '''
import os
from queue import Queue

import colorama
import xlsxwriter

from modules.list_metadata.parser import parse_metadata
from modules.list_metadata.retriever import retrieve_metadata
from modules.utils import INFO_TAG, erase_file

FOLDER_LIST = []

WARNING_QUEUE = Queue()
ERROR_QUEUE = Queue()


def generate_parser(parser, is_build_xml):
    ''' Parse args method for  '''
    if is_build_xml:
        parser.add_argument('--source', '-s', nargs='*', metavar='source',
                            dest='sources', required=True,
                            help='Sources from which retrieve data')
    else:
        parser.add_argument('--sources', '-s', nargs='*', required=True,
                            help='Sources from which retrieve data')
    parser.add_argument('--metadata_types', '-t', nargs='*',
                        help='Metadata types to list in XML Format')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Outputs ant to standard output')
    parser.add_argument('--local', '-l', action='store_true',
                        help='Use local data from list folder')
    parser.add_argument('--result-file', '-r', default='result-file',
                        help='Specifies the result file, default=result_file')
    return parser


def run(args):
    ''' Method to be runned from other package '''
    metadata_types = retrieve_metadata(args.sources, args.metadata_types,
                                       args.verbose, args.local)
    metadatas = parse_metadata(metadata_types, args.sources)
    if metadatas:
        if 'build_xml' in args.option:
            __create_result_package(args.result_file, metadatas)
        elif 'compare_meta' in args.option:
            __create_result_xlsx(args.result_file, metadatas)


def __create_result_xlsx(file_name, metadatas):
    ''' Creates an Excel file with the result '''
    file_path = f'{file_name}.xlsx'
    erase_file(file_path)
    print(f'{INFO_TAG} Saving XLSX into \'{file_path}\'')
    workbook = xlsxwriter.Workbook(file_path)
    unique_format = workbook.add_format({'bg_color': '#FFC7CE',
                                         'font_color': '#9C0006'})
    for metadata in metadatas:
        metadata.to_worksheet(workbook, unique_format)


def __create_result_package(file_name, metadatas):
    ''' Creates an XML file with the result '''
    file_path = f'{file_name}.xml'
    print(f'{INFO_TAG} Saving XML into \'{file_path}\'')
    os.remove(file_path) if os.path.exists(file_path) else None
    with open(file_path, 'w') as file_handler:
        file_handler.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        file_handler.write('\t<Package xmlns='
                           '"http://soap.sforce.com/2006/04/metadata">\n')
        for metadata in metadatas:
            file_handler.write(f'{metadata.to_package_xml()}\n')
        file_handler.write('\t<version>41.0</version>\n')
        file_handler.write('</Package>\n')


if __name__ == '__main__':
    colorama.init()
