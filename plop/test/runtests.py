#!/usr/bin/env python

import sys
import unittest

TEST_MODULES = [
    'plop.test.collector_test',
    'plop.test.platform_test',
    'plop.test.callgraph_test',
    ]

def all():
    return unittest.defaultTestLoader.loadTestsFromNames(TEST_MODULES)

if __name__ == '__main__':
    import tornado.testing
    tornado.testing.main()
