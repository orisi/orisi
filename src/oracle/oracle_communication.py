# File responsible for sending messages according to protocol`

from bitmessage_communication.bitmessageclient import BitmessageClient
from oracle_protocol import (
    PING_SUBJECT,
    PING_MESSAGE,
    IDENTITY_SUBJECT,
    IDENTITY_MESSAGE,
    PROTOCOL_REGEX)

import re

class OracleCommunication:

  def __init__(self):
    self.client = BitmessageClient()

    # Do we really need it here?
    self.default_address = self.client.default_address

  def corresponds_to_protocol(self, message):
    for pattern, operation in PROTOCOL_REGEX:
      if re.match(pattern, message.message):
        return operation
      if re.match(pattern, message.subject):
        return operation
    return False

  def get_new_requests(self):
    messages = self.client.get_unread_messages()
    requests = []
    for msg in messages:
      operation = self.corresponds_to_protocol(msg)
      if operation:
        requests.append((operation, msg))
      else:
        # If message is not corresponding to protocol, then mark it as read
        # All other messages will me marked later
        self.client.mark_message_as_read(msg)
    return requests

  def mark_request_done(self, request):
    operation, message = request
    self.client.mark_message_as_read(message)

  def ping_response(self, address):
    self.client.send_message(
        address, 
        PING_SUBJECT, 
        PING_MESSAGE)

  def broadcast_identity(self):
    self.client.send_broadcast(
        IDENTITY_SUBJECT,
        IDENTITY_MESSAGE)