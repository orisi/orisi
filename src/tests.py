#!/usr/bin/env python2.7
from oracle.tests import OracleTests
from client.tests import ClientTests

import unittest

TESTS = [
   OracleTests,
   ClientTests,
]

def test():
  suite = []
  for test_cls in TESTS:
    st = unittest.TestLoader().loadTestsFromTestCase(test_cls)
    suite.append(st)
  suite = unittest.TestSuite(suite)
  unittest.TextTestRunner(verbosity=2).run(suite)

if __name__=="__main__":
  print "Our tests doesnt work currently"
  exit()
  test()

