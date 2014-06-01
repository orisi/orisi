import xmlrpclib
import json
import base64

from settings_local import (
  BITMESSAGE_USERNAME,
  BITMESSAGE_PASSWORD,
  BITMESSAGE_HOST,
  BITMESSAGE_PORT)

api = xmlrpclib.ServerProxy("http://%s:%s@%s:%s" % 
    (
      BITMESSAGE_USERNAME, 
      BITMESSAGE_PASSWORD, 
      BITMESSAGE_HOST, 
      BITMESSAGE_PORT))

print api.add(1,3)