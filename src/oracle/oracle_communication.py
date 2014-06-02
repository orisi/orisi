from bitmessage_communication.bitmessageclient import BitmessageClient

class OracleCommunication:

  def __init__(self):
    self.client = BitmessageClient()
    self.default_address = self.get_default_address()

  def get_default_address(self):
    # We want to get default address with label 'oracle'
    default_address = self.find_default_address()

    if not default_address:
      self.client.create_random_address()
      default_address = self.find_default_address()
    return default_address

  def find_default_address(self):
    default_address = None
    for address in self.client.addresses:
      if address.label == 'oracle':
        default_address = address
        break
    return default_address