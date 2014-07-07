# File responsible for sending messages according to protocol`
from shared.bitmessage_communication.bitmessageclient import BitmessageClient

from handlers.handlers import op_handlers

from handlers.handlers import (
    PROTOCOL_VERSION,
    OPERATION_REQUIRED_FIELDS)

import json
import logging

class OracleCommunication:

  def __init__(self):
    self.client = BitmessageClient()

    # Do we really need it here?
    self.default_address = self.client.default_address
    logging.info("my BM address: %r" % self.client.default_address)


  def corresponds_to_protocol(self, message):
    try:
      body = json.loads(message.message)
    except ValueError:
      logging.info('message is not a valid json')
      return False
    if not 'operation' in body:
      logging.info('message has no operation')
      return False

    if not body['operation'] in op_handlers:
      logging.info('operation %r not supported' % body['operation'])
      return False

    operation = body['operation']

    if operation in OPERATION_REQUIRED_FIELDS:
      required_fields = OPERATION_REQUIRED_FIELDS[operation]
      for field in required_fields:
        if not field in body:
          logging.info('required field {0} for operation {1} missing'.format(field, operation))
          return False
    else:
      logging.warning('operation %r has no OPERATION_REQUIRED_FIELDS defined' % operation)

    logging.info('operation {0}'.format(operation))
    return operation

  def get_new_requests(self):
    messages = self.client.get_unread_messages()
    requests = []
    for msg in messages:
      if msg.direct:
        self.response(msg, 'DirectMessage', 'direct message unsupported')
        continue
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

  def response(self, message, subject, response):
    self.response_to_address(message.from_address, subject, response)

  def response_to_address(self, address, subject, response):
    body = {}
    body['version'] = PROTOCOL_VERSION
    body['response'] = response
    body_json = json.dumps(body)
    self.client.send_message(
        address,
        subject,
        body_json)


  def broadcast(self, subject, message):
    self.client.send_message(self.client.chan_address, subject, message)




  def broadcast_identity(self):

    IDENTITY_MESSAGE_RAW = {
      "response": "active",
      "version": PROTOCOL_VERSION
    }

    self.client.send_broadcast(
        'IdentityBroadcast',
        json.dumps(IDENTITY_MESSAGE_RAW))
