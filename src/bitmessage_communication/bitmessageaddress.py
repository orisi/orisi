import base64

class BitmessageAddress:
  def __init__(self, address_dict):
    self.chan = address_dict['chan']
    self.address = address_dict['address']
    self.enabled = address_dict['enabled']
    self.stream = address_dict['stream']
    self.encoded_label = address_dict['label']
    self.label = base64.decodestring(self.encoded_label)

  def __repr__(self):
    return "{0} - {1}".format(self.label, self.address)