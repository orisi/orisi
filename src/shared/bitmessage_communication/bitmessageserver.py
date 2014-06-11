from settings_local import *

from bitmessageexceptions import EXCEPTION_API

import xmlrpclib
import json
import base64
import re

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

    self.api = xmlrpclib.ServerProxy("http://{0}:{1}@{2}:{3}".format(
        BITMESSAGE_USERNAME,
        BITMESSAGE_PASSWORD,
        BITMESSAGE_HOST,
        BITMESSAGE_PORT))

  def call_with_exception(self, name):
    def foo(*args, **kwargs):
      result = self.api.__getattr__(name)(*args, **kwargs)
      check_exception(result)
      return result
    return foo

  def __getattr__(self, name):
    return self.call_with_exception(name)

