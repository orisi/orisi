from oracle import tests
from oracle.oracle import Oracle

import sys
import unittest

TESTS = [
  tests.OracleTests,
]

def test():
  suite = []
  for test_cls in TESTS:
    st = unittest.TestLoader().loadTestsFromTestCase(test_cls)
    suite.append(st)
  suite = unittest.TestSuite(suite)
  results = unittest.TestResult()
  unittest.TextTestRunner(verbosity=2).run(suite)
