# File responsible for sending messages according to protocol`

from bitmessage_communication.bitmessageclient import BitmessageClient

from oracle_protocol import (
    PING_SUBJECT,
    PING_MESSAGE)

class OracleCommunication:

  def __init__(self):
    self.client = BitmessageClient()

    # Do we really need it here?
    self.default_address = self.client.default_address

  def ping_response(self, address):
    self.client.send_message(
        address, 
        PING_SUBJECT, 
        PING_MESSAGE)