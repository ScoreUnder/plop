import ast
import logging
import threading
import time
import unittest
import six

from plop.collector import Collector, PlopFormatter


def _filter_stacks(collector):
    # Kind of hacky, but this is the simplest way to keep the tests
    # working after the internals of the collector changed to support
    # multiple formatters.
    stack_counts = ast.literal_eval(PlopFormatter().format(collector))
    counts = {}
    for stack, count in six.iteritems(stack_counts):
        filtered_stack = [frame[2] for frame in stack
                          if frame[0].endswith('collector_test.py')]
        if filtered_stack:
            counts[tuple(filtered_stack)] = count
    return counts


class CollectorTest(unittest.TestCase):
    def check_counts(self, counts, expected):
        failed = False
        output = []
        for stack, count in six.iteritems(expected):
            # every expected frame should appear in the data, but
            # the inverse is not true if the signal catches us between
            # calls.
            self.assertTrue(stack in counts)
            ratio = float(counts[stack])/float(count)
            output.append('%s: expected %s, got %s (%s)' %
                          (stack, count, counts[stack], ratio))
            if not 0.70 <= ratio <= 1.25:
                failed = True
        if failed:
            for line in output:
                logging.warning(line)
            for key in set(counts.keys()) - set(expected.keys()):
                logging.warning('unexpected key: %s: got %s', key, counts[key])
            self.fail("collected data did not meet expectations")

    def test_collector(self):
        """ the collector can sample the stack """
        start = time.time()
        def example_a(end):
            while time.time() < end:
                pass
            example_c(time.time() + 0.1)
        def example_b(end):
            while time.time() < end:
                pass
            example_c(time.time() + 0.1)
        def example_c(end):
            while time.time() < end:
                pass
        collector = Collector(interval=0.01, mode='prof')
        collector.start()
        example_a(time.time() + 0.1)
        example_b(time.time() + 0.2)
        example_c(time.time() + 0.3)
        end = time.time()
        collector.stop()
        elapsed = end - start
        self.assertTrue(0.8 < elapsed < 0.9, elapsed)

        counts = _filter_stacks(collector)

        expected = {
            ('example_a', 'test_collector'): 10,
            ('example_c', 'example_a', 'test_collector'): 10,
            ('example_b', 'test_collector'): 20,
            ('example_c', 'example_b', 'test_collector'): 10,
            ('example_c', 'test_collector'): 30,
            }
        self.check_counts(counts, expected)

        # cost depends on stack depth; for this tiny test I see 40-80usec
        time_per_sample = float(collector.sample_time) / collector.samples_taken
        self.assertTrue(time_per_sample < 0.000100, time_per_sample)

    # TODO: any way to make this test not flaky?
    def disabled_test_collect_threads(self):
        start = time.time()
        def example_a(end):
            while time.time() < end:
                pass
        def thread1_func():
            example_a(time.time() + 0.2)
        def thread2_func():
            example_a(time.time() + 0.3)
        collector = Collector(interval=0.01, mode='prof')
        collector.start()
        thread1 = threading.Thread(target=thread1_func)
        thread2 = threading.Thread(target=thread2_func)
        thread1.start()
        thread2.start()
        example_a(time.time() + 0.1)
        while thread1.isAlive() or thread2.isAlive():
            pass
        thread1.join()
        thread2.join()
        end = time.time()
        collector.stop()
        elapsed = end - start
        self.assertTrue(0.3 < elapsed < 0.4, elapsed)

        counts = _filter_stacks(collector)

        expected = {
            ('example_a', 'test_collect_threads'): 10,
            ('example_a', 'thread1_func'): 20,
            ('example_a', 'thread2_func'): 30,
            }
        self.check_counts(counts, expected)
