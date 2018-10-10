''' Flask rest server for tests '''
import atexit

import argparse
import colorama
from flask import Flask, request, abort, make_response

from utils import serialize_response, INFO_TAG
from seleniumrunner import SeleniumRunner


def __parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--threads', '-t', type=int, default=1, required=True)
    parser.add_argument('--verbose', '-v', action='store_true')
    return parser.parse_args()


def __force_close():
    HANDLER.close_drivers()
    exit(0)


ARGS = __parse_args()
colorama.init()
HANDLER = SeleniumRunner(ARGS.threads, ARGS.verbose)
APP = Flask(__name__)
atexit.register(__force_close)


@APP.route('/')
def run_tests_for_thread():
    ''' Default endpoint '''
    thread_number = int(request.args.get('number', -1)) - 1
    print(f'{INFO_TAG} Received Request for Thread-{thread_number}')
    if thread_number < ARGS.threads:
        results = HANDLER.run_tests_for(int(thread_number))
        status = results.get_status()
        message = 'Tests finished Correctly' if status else 'Tests finished with errors'
        status = 'OK' if status else 'KO'
        return serialize_response('200', status, message, results.serialize())
    abort(404, f'Thread {thread_number} out of bounds')


@APP.errorhandler(400)
def __bad_request(error):
    ''' Bad Request Handler '''
    return make_response(serialize_response(400, 'Bad Request',
                                            error.description), 400)


@APP.errorhandler(404)
def __not_found(error):
    ''' Not Found Handler '''
    return make_response(serialize_response(404, 'Not Found',
                                            error.description), 404)


if __name__ == '__main__':
    PORT_NUMBER = 5000
    print(f'{INFO_TAG} Starting WebServer on port {PORT_NUMBER}, press control+c to quit')
    APP.run(threaded=True, port=PORT_NUMBER)
