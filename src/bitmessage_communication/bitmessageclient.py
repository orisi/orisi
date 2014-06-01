from bitmessageaddress import BitmessageAddress
from settings_local import (
    BITMESSAGE_USERNAME,
    BITMESSAGE_PASSWORD,
    BITMESSAGE_HOST,
    BITMESSAGE_PORT)

import xmlrpclib
import json
import base64

class BitmessageClient:

  def __init__(self):
    self.connect()
    self.get_addresses()

  def connect(self):
    self.api = xmlrpclib.ServerProxy("http://{0}:{1}@{2}:{3}".format(
        BITMESSAGE_USERNAME,
        BITMESSAGE_PASSWORD,
        BITMESSAGE_HOST,
        BITMESSAGE_PORT))

  def get_addresses(self):
    addresses_json = self.api.listAddresses2()
    address_list = json.loads(addresses_json)['addresses']

    self.addresses = \
        [BitmessageAddress(address_dict) for address_dict in address_list]

bmc = BitmessageClient()
