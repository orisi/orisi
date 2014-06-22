#!/usr/bin/env python2.7
from shared import logger
from oracle.oracle import Oracle

def main():
  logger.init_logger()
  o = Oracle()
  o.run()

if __name__=="__main__":
  main()
