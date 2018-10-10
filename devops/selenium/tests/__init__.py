''' EI '''
class Test():
    ''' Abstract Test Class '''
    def run(self):
        ''' Runs the implemented test '''
        raise NotImplementedError('AbstractClass')

    def get_error_message(self):
        ''' Returns string with the error message '''
        raise NotImplementedError('AbstractClass')
