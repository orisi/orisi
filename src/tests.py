from oracle import tests
from oracle.oracle import Oracle

import sys
import unittest

TESTS = [
  tests.OracleTests,
]

def present_results(results):
  print "Tests Run: {}".format(results.testsRun)
  print "Errors: {}".format(len(results.errors))
  for error in results.errors:
    print "____"
    print "{}.{}".format(error[0].__class__.__name__, error[0]._testMethodName)
    print 
    print error[1]

def test():
  suite = []
  for test_cls in TESTS:
    st = unittest.TestLoader().loadTestsFromTestCase(test_cls)
    suite.append(st)
  suite = unittest.TestSuite(suite)
  results = unittest.TestResult()
  suite.run(results)

  present_results(results)