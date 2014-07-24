from settings_local import *

from bitmessageexceptions import EXCEPTION_API

import xmlrpclib
import re
import time
import logging

def check_exception(result):
  number = get_exception_number(result)
  if number:
    raise EXCEPTION_API[str(number)](result)

def get_exception_number(result):
  r = re.match(r'^API Error (\d{4}):.*$', result)
  if not r:
    return None
  return r.group(1)

class BitmessageServer:
  def __init__(self):
    try_factor = 1

    while 1:
      try:
        self.api = xmlrpclib.ServerProxy("http://{0}:{1}@{2}:{3}".format(
            BITMESSAGE_USERNAME,
            BITMESSAGE_PASSWORD,
            BITMESSAGE_HOST,
            BITMESSAGE_PORT))
        self.api.helloWorld('x', 'y')
        return
      except:
        try_factor *= 2

        if try_factor > 512:
          logging.critical('can\'t connect to bitmessage server')
          return

        logging.info('can\'t connect to bitmessage server, waiting {}'.format(try_factor))
        time.sleep(try_factor)

  def call_with_exception(self, name):
    def foo(*args, **kwargs):
      result = self.api.__getattr__(name)(*args, **kwargs)
      check_exception(result)
      return result
    return foo

  def __getattr__(self, name):
    return self.call_with_exception(name)

