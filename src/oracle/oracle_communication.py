# File responsible for sending messages according to protocol`

from bitmessage_communication.bitmessageclient import BitmessageClient
from oracle_protocol import (
    PING_SUBJECT,
    PING_MESSAGE,
    IDENTITY_SUBJECT,
    IDENTITY_MESSAGE,
    VALID_OPERATIONS,
    OPERATION_REQUIRED_FIELDS)

import json
import logging

class OracleCommunication:

  def __init__(self):
    self.client = BitmessageClient()

    # Do we really need it here?
    self.default_address = self.client.default_address

  def corresponds_to_protocol(self, message):
    try:
      body = json.loads(message.message)
    except ValueError:
      logging.info('message is not a valid json')
      return False
    if not 'operation' in body:
      logging.info('message has no operation')
      return False

    if not body['operation'] in VALID_OPERATIONS.iterkeys():
      logging.info('operation not supported')
      return False

    operation = VALID_OPERATIONS[body['operation']]

    required_fields = OPERATION_REQUIRED_FIELDS[operation]
    for field in required_fields:
      if not field in body:
        logging.info('required field {0} for operation {1} missing'.format(field, operation))
        return False

    logging.info('operation {0}'.format(operation))
    return operation

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

  def response(self, message, subject, response):
    body = RAW_RESPONSE
    body['response'] = response
    body_json = json.dumps(body)
    self.client.send_message(
        message.from_address,
        subject,
        body_json)

  def broadcast_identity(self):
    self.client.send_broadcast(
        IDENTITY_SUBJECT,
        IDENTITY_MESSAGE)