''' Test classes '''
class AbstractTest():
    ''' Abstract Test Class '''
    def run(self):
        ''' Runs the implemented test '''
        raise NotImplementedError('AbstractClass')

    def get_error_message(self):
        ''' Returns string with the error message '''
        raise NotImplementedError('AbstractClass')


class TestResult:
    ''' Wrapper to save test result data '''
    def __init__(self, test_name, result, message, elapsed):
        self.test_name = test_name
        self.test_result = result
        self.test_message = message
        self.elapsed = elapsed

    def serialize(self):
        ''' Serializes object into dictionary '''
        return {"test_name": self.test_name, "test_result": self.test_result,
                "message": self.test_message, "time": self.elapsed}


class TestResultBundle:
    ''' Wrapper of test result bundle '''
    def __init__(self, name='TestBundle'):
        self.correct_tests = 0
        self.tests_time = 0
        self.tests = []
        self.name = name

    def __repr__(self):
        return f'<{self.name}, {self.correct_tests}/{len(self.tests)}>'

    def get_status(self):
        ''' Returns if all the tests have been run succesfully '''
        return len(self.tests) == self.correct_tests

    def add_test_result(self, test):
        ''' Adds a testresult to the list of tests results '''
        self.correct_tests += 1 if test.test_result else 0
        self.tests_time += test.elapsed
        self.tests.append(test)

    def serialize(self):
        ''' Serializes data into a dictionary '''
        test_status = self.get_status()
        return {"tests_status": test_status, "tests_time": self.tests_time,
                "tests_stats": f'{self.correct_tests}/{len(self.tests)}',
                "tests_results": [test.serialize() for test in self.tests]}
