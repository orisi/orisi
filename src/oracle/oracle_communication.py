# File responsible for sending messages according to protocol

from bitmessage_communication.bitmessageclient import BitmessageClient

from oracle_protocol import PROTOCOL_ORACLE_IDENTITY

class OracleCommunication:

  def __init__(self):
    self.client = BitmessageClient()

    # Do we really need it here?
    self.default_address = self.client.default_address

  def broadcast_identity(self):
    subject = PROTOCOL_ORACLE_IDENTITY

    # TODO - what should we add to Identity Broadcast? Maybe public key for verifications?
    # or maybe list of known other oracles?
    message = PROTOCOL_ORACLE_IDENTITY
    self.client.send_broadcast(subject, message)
