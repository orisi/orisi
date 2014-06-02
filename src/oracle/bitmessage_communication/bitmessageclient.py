from bitmessageaddress import BitmessageAddress
from bitmessagemessage import BitmessageMessage
from bitmessageserver import BitmessageServer
from settings_local import DEFAULT_ADDRESS_LABEL

import xmlrpclib
import json
import base64
import re

class BitmessageClient:

  def __init__(self):
    self.connect()
    self.get_addresses()
    self.update_address_if_empty()

  def connect(self):
    self.api = BitmessageServer()

  def create_random_address(self, label=DEFAULT_ADDRESS_LABEL):
    label_base64 = base64.encodestring(label)
    self.api.createRandomAddress(label_base64)
    self.get_addresses()

  def get_addresses(self):
    addresses_json = self.api.listAddresses2()
    address_list = json.loads(addresses_json)['addresses']

    self.addresses = \
        [BitmessageAddress(address_dict) for address_dict in address_list]
    self.enabled_addresses = \
        [addr for addr in self.addresses if addr.enabled]

    if len(self.enabled_addresses) > 0:
      self.default_address = self.enabled_addresses[0]

    for address in self.enabled_addresses:
      if address.label == DEFAULT_ADDRESS_LABEL:
        self.default_address = address
        break

  def update_address_if_empty(self):
    if len(self.addresses) > 0:
      return
    self.create_random_address()

  def send_message(self, address, subject, message):
    ack_data = self.api.sendMessage(
                  address, 
                  self.default_address.address, 
                  base64.encodestring(subject),
                  base64.encodestring(message))
    return ack_data

  def send_broadcast(self, subject, message):
    ack_data = self.api.sendBroadcast(
                  self.default_address.address,
                  base64.encodestring(subject),
                  base64.encodestring(message))
    return ack_data

  def get_inbox(self):
    messages_json = self.api.getAllInboxMessages()
    messages_list = json.loads(messages_json)['inboxMessages']

    messages_inbox = \
        [BitmessageMessage(msg) for msg in messages_list]

    return messages_inbox

  def get_unread_messages(self):
    messages = self.get_inbox()
    unread_messages = [msg for msg in messages if not msg.read]
    return unread_messages

  def mark_message_as_read(self, msgid):
    self.api.getInboxMessageByID(msgid, True)

  def mark_message_as_unread(self, msgid):
    self.api.getInboxMessageByID(msgid, False)

  def trash_message(self, msgid):
    self.api.trashMessage(msgid)

  def delete_address(self, address):
    self.api.deleteAddress(address)
