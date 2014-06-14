from shared import logger
from oracle.oracle import Oracle
from tests import test

import sys

def main():
  if len(sys.argv) > 1 and sys.argv[1].lower() == 'test':
    test()
    return
  logger.init_logger()
  o = Oracle()
  o.run()

if __name__=="__main__":
  main()
