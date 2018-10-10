''' Module for parsing the tokens from the files '''
from modules.utils import (DATA_TAG, FOLDERED_ITEMS, INFO_TAG, WARNING_TAG,
                           CompoundTokenDetectedException,
                           EmptyTokenListException, get_filenames,
                           get_key_value)

FULLNAME = 'FullName/Id: '
CREATED_BY = 'Created By (Name/Id): '
MODIFIED_BY = 'Last Modified By (Name/Id): '
MANAGEABLE_STATE = 'Manageable State: '
PREFIX_NAME = 'Namespace Prefix: '

PARENT_CHILD_HEADER = {'columns': [{'header': 'Parent Name'},
                                   {'header': 'Child Name'},
                                   {'header': 'API Name'},
                                   {'header': 'Created By'},
                                   {'header': 'Modified By'},
                                   {'header': 'Environment'},
                                   {'header': 'Manegeable State'},
                                   {'header': 'Prefix Name'}]}

FLOW_HEADER = {'columns': [{'header': 'Flow Name'},
                           {'header': 'Flow Version'},
                           {'header': 'API Name'},
                           {'header': 'Created By'},
                           {'header': 'Modified By'},
                           {'header': 'Environment'},
                           {'header': 'Manegeable State'},
                           {'header': 'Prefix Name'}]}

SIMPLE_HEADER = {'columns': [{'header': 'API Name'},
                             {'header': 'Created By'},
                             {'header': 'Modified By'},
                             {'header': 'Environment'},
                             {'header': 'Manegeable State'},
                             {'header': 'Prefix Name'}]}

PARENT_CHILD_HEADER = {'columns': [{'header': 'Folder Name'},
                                   {'header': 'Item Name'},
                                   {'header': 'API Name'},
                                   {'header': 'Created By'},
                                   {'header': 'Modified By'},
                                   {'header': 'Environment'},
                                   {'header': 'Manegeable State'},
                                   {'header': 'Prefix Name'}]}


def _configurator(api_type=None):
    if api_type in FOLDERED_ITEMS:
        return {'header': PARENT_CHILD_HEADER, 'token': FolderedToken,
                'id_column': 'C2:C{}',
                'bounds': 'A1:{}{}', 'width': [30, 40, 70, 22, 22, 15, 30, 30]}
    if api_type == 'Flow':
        return {'header': FLOW_HEADER, 'token': FlowToken,
                'id_column': 'C2:C{}',
                'bounds': 'A1:{}{}', 'width': [35, 15, 45, 22, 22, 15, 30, 30]}
    if api_type == 'DOUBLE':
        return {'header': PARENT_CHILD_HEADER, 'token': CompoundToken,
                'id_column': 'C2:C{}',
                'bounds': 'A1:{}{}', 'width': [30, 40, 70, 22, 22, 15, 30, 30]}
    return {'header': SIMPLE_HEADER, 'token': Token, 'id_column': 'A2:A{}',
            'bounds': 'A1:{}{}', 'width': [30, 30, 30, 30, 30, 30]}


def _get_nth_letter(header):
    header_length = len(header['columns'])
    return chr(ord('A') + header_length - 1)


class MetadataType:
    ''' MetadataType Object '''
    def __repr__(self):
        return f'<{self.api_name}, {self.environments}>'

    def __init__(self, name, environments):
        self.api_name = name
        self.environments = environments
        self.tokens = []
        configuration_params = _configurator(self.api_name)
        self.token_type = configuration_params['token']
        self.header = configuration_params['header']
        self.id_column = configuration_params['id_column']
        self.bounds = configuration_params['bounds']
        self.width = configuration_params['width']
        self.__initialize_token_list()
        if not self.tokens:
            raise EmptyTokenListException()

    def __initialize_token_list(self):
        ''' Parses data from file '''
        second_asterisk = False
        compound_token = False
        item_lines = []
        for environment in self.environments:
            lines = _get_lines(environment, self.api_name)
            for line in lines:
                if line.startswith('*') and not second_asterisk:
                    item_lines = []
                    second_asterisk = True
                elif line.startswith('*'):
                    try:
                        self.tokens.append(self.token_type(item_lines,
                                                           environment))
                    except CompoundTokenDetectedException:
                        compound_token = True
                        self.__change_to_compound_configuration()
                        self.tokens.append(self.token_type(item_lines,
                                                           environment))
                    second_asterisk = False
                else:
                    item_lines.append(line)
        if compound_token:
            self.__migrate_sigle_to_compound()

    def __migrate_sigle_to_compound(self):
        new_list = []
        for token in self.tokens:
            new_list.append(CompoundToken(token))
        self.tokens = new_list

    def __change_to_compound_configuration(self):
        configuration_params = _configurator('DOUBLE')
        self.token_type = configuration_params['token']
        self.header = configuration_params['header']
        self.id_column = configuration_params['id_column']
        self.bounds = configuration_params['bounds']
        self.width = configuration_params['width']

    def to_package_xml(self):
        ''' Generates the package xml for a type '''
        result = '\t<types>\n'
        result += ''.join([f'\t\t{metadata_token.to_package_format()}\n'
                           for metadata_token in self.tokens])
        result += f'\t\t<name>{self.api_name}</name>\n'
        result += '\t</types>'
        return result

    def to_worksheet(self, workbook, unique_format, worksheet=None):
        ''' Extracts the tokens to the passed worksheet '''
        print(f'{INFO_TAG} Building sheet for {self.api_name}')
        if not worksheet:
            worksheet = workbook.add_worksheet(self.api_name)
        for row, token_ in enumerate(self.tokens):
            token_.extract_to_worksheet(row + 1, worksheet)
        worksheet.add_table(self.bounds.format(_get_nth_letter(self.header),
                                               len(self.tokens) + 1),
                            self.header)
        for index, value in enumerate(self.width):
            worksheet.set_column(index, len(self.tokens), value)
        if len(self.environments) > 1 and len(self.tokens) > 1:
            value = self.id_column.format(len(self.tokens) + 1)
            cell_format = {'type': 'unique', 'format': unique_format}
            worksheet.conditional_format(value, cell_format)


def _get_lines(environment, metadata_type):
    file_paths = get_filenames(environment, metadata_type)
    file_str = ''
    for file_path in file_paths:
        file = open(file_path, 'r')
        file_str += file.read()
    return file_str.split('\n')


class Token:
    ''' Token Object '''
    def __repr__(self):
        return f'<Token: \'{self.api_name}\'>'

    def __str__(self):
        result = f'{DATA_TAG}: '
        result += f'{get_key_value("api_name", self.api_name)} '
        result += f'{get_key_value("created by", self.created_by)} '
        result += f'{get_key_value("last modified by", self.last_modified_by)}'
        result += f'{get_key_value("environment", self.environment)}'
        return result

    def __init__(self, list_log, environment):
        self.api_name = ''
        self.created_by = ''
        self.last_modified_by = ''
        self.environment = environment
        self.manageable_state = ''
        self.namespace_prefix = ''
        self.__parse_log(list_log)

    def __parse_log(self, list_log):
        for line in list_log:
            if line.startswith(FULLNAME):
                self.api_name = (line[len(FULLNAME):-1
                                      if line.endswith('/') else -19])
            if line.startswith(CREATED_BY):
                self.created_by = line[len(CREATED_BY):-19]
            if line.startswith(MODIFIED_BY):
                self.last_modified_by = line[len(MODIFIED_BY):-19]
            if line.startswith(MANAGEABLE_STATE):
                self.manageable_state = line[len(MANAGEABLE_STATE):]
            if line.startswith(PREFIX_NAME):
                self.namespace_prefix = line[len(PREFIX_NAME):]
        if (self.__class__.__name__ == Token.__name__
                and ('-' in self.api_name or '.' in self.api_name)):
            raise CompoundTokenDetectedException()

    def to_package_format(self):
        ''' Returns the token in package.xml format '''
        return f'<members>{self.api_name}</members>'

    def extract_to_worksheet(self, row_number, worksheet_):
        ''' Extracts the information to the passed worksheet '''
        row = f'{self.api_name};{self.created_by};{self.last_modified_by};'
        row += (f'{self.environment};{self.manageable_state};'
                f'{self.namespace_prefix}')
        worksheet_.write_row(row_number, 0, row.split(';'))


class FlowToken(Token):
    ''' Metadata token for Flow Items '''
    def extract_to_worksheet(self, row_number, worksheet_):
        ''' Extracts the information to the passed worksheet '''
        splitted = self.api_name.split('-')
        flow_name = splitted[0]
        flow_version = 0 if len(splitted) == 1 else int(splitted[1])
        worksheet_.write(row_number, 0, flow_name)
        worksheet_.write_number(row_number, 1, flow_version)
        row = (f'{self.api_name};{self.created_by};{self.last_modified_by};'
               f'{self.environment};')
        row += f'{self.manageable_state};{self.namespace_prefix}'
        worksheet_.write_row(row_number, 2, row.split(';'))


class CompoundToken(Token):
    ''' Compound token type for api name + subapi name '''
    def __init__(self, token, environment=None):
        if not environment:
            self.api_name = token.api_name
            self.created_by = token.created_by
            self.last_modified_by = token.last_modified_by
            self.environment = token.environment
            self.manageable_state = token.manageable_state
            self.namespace_prefix = token.namespace_prefix
        else:
            super(CompoundToken, self).__init__(token, environment)

    def extract_to_worksheet(self, row_number, worksheet_):
        ''' Extracts the information to the passed worksheet '''
        splitted = self.api_name.replace('-', '.').split('.')
        parent_object = splitted[0]
        worksheet_.write(row_number, 0, parent_object)
        if len(splitted) > 1:
            child_object = splitted[1]
            worksheet_.write(row_number, 1, child_object)
        row = (f'{self.api_name};{self.created_by};{self.last_modified_by};'
               f'{self.environment};')
        row += f'{self.manageable_state};{self.namespace_prefix}'
        worksheet_.write_row(row_number, 2, row.split(';'))


class FolderedToken(Token):
    ''' Compound token type for api name + subapi name '''
    def __init__(self, list_log, environment):
        self.api_name = ''
        self.folder_name = ''
        self.folder_item = ''
        self.created_by = ''
        self.last_modified_by = ''
        self.environment = environment
        self.manageable_state = ''
        self.namespace_prefix = ''
        self.__parse_log(list_log)

    def extract_to_worksheet(self, row_number, worksheet_):
        ''' Extracts the information to the passed worksheet '''
        splitted = self.api_name.split('/')
        parent_object = splitted[0]
        worksheet_.write(row_number, 0, parent_object)
        if len(splitted) > 1:
            child_object = splitted[1]
            worksheet_.write(row_number, 1, child_object)
        row = (f'{self.api_name};{self.created_by};{self.last_modified_by};'
               f'{self.environment};')
        row += f'{self.manageable_state};{self.namespace_prefix}'
        worksheet_.write_row(row_number, 2, row.split(';'))

    def __parse_log(self, list_log):
        for line in list_log:
            if line.startswith(FULLNAME):
                self.api_name = (line[len(FULLNAME):-1
                                      if line.endswith('/') else -19])
            if line.startswith(CREATED_BY):
                self.created_by = line[len(CREATED_BY):-19]
            if line.startswith(MODIFIED_BY):
                self.last_modified_by = line[len(MODIFIED_BY):-19]
            if line.startswith(MANAGEABLE_STATE):
                self.manageable_state = line[len(MANAGEABLE_STATE):]
            if line.startswith(PREFIX_NAME):
                self.namespace_prefix = line[len(PREFIX_NAME):]


def parse_metadata(metadata_types, sources):
    ''' main method for parser package, parses metadata for the types and
        sources passed returns the resulting metadata tokens '''
    metadata_tokens = []
    for metadata_type in metadata_types:
        try:
            metadata_tokens.append(MetadataType(metadata_type, sources))
        except EmptyTokenListException:
            print(f'{WARNING_TAG} Empty Token List for {metadata_type}')
    return metadata_tokens
