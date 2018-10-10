''' Module to measure the load times '''
import statistics

from seleniumrunner.tests import TestResult, AbstractTest

from utils import start_timer, stop_timer, INFO_TAG, get_random_color

class PageLoadTest(AbstractTest):
    '''  '''
    def __init__(self, driver, pages, number_of_iterations=5, erase_min_max=True):
        self.driver = driver
        self.pages = pages
        self.results = {}
        self.number_of_iterations = number_of_iterations
        self.erase_min_max = erase_min_max

    def run(self):
        print(f'{INFO_TAG} Starting Page Load Test with {self.number_of_iterations} iterations')
        for i in range(self.number_of_iterations):
            start_time = start_timer()
            self.__iterate_over_pages()
            elapsed_time = stop_timer(start_time)
            print(f'{INFO_TAG} Finished {i + 1} wave in {elapsed_time} ms')
        print(list(self.results.values()))

    def __iterate_over_pages(self):
        for page in self.pages:
            elapsed_time = self.__measure_time(page)
            print(f'{INFO_TAG} Page {page} loaded in {elapsed_time} ms')
            time_result = self.results.get(page, TimeTestResult(page))
            time_result.add_time(elapsed_time)
            self.results[page] = time_result
            # input('CONTINUE')

    def get_error_message(self):
        pass

    def __measure_time(self, page):
        start_time = start_timer()
        self.driver.get_local(f'/apex/{page}')
        return stop_timer(start_time)


class TimeTestResult:
    def __init__(self, page):
        self.page = page
        self.times = []

    def __repr__(self):
        return get_random_color(f'<{self.page}, n={len(self.times)} μ={self.get_mean()}ms>')

    def add_time(self, time):
        self.times.append(time)

    def erase_edges(self):
        self.times.sort()
        return self.times[1:-1]

    def get_mean(self, times=None):
        times = times if times else self.times
        return round(statistics.mean(times), 2)

    def serialize(self):
        erased_edges = self.erase_edges
        return {'page': self.page, 'times': erased_edges, 'mean': self.get_mean(erased_edges)}
