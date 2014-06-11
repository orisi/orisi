import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from settings_local import *

from bitmessageaddress import BitmessageAddress
from bitmessagemessage import BitmessageMessage
from bitmessageserver import BitmessageServer
from bitmessageexceptions import ChanAlreadySubscribedException

import xmlrpclib
import json
import base64
import re
import logging

class BitmessageClient:

  def __init__(self, default_address_label=DEFAULT_ADDRESS_LABEL):
    self.default_address_label = default_address_label
    self.connect()
    self.get_addresses()
    self.update_address_if_empty()
    self.chan_address = CHAN_ADDRESS
    self.join_chan(CHAN_NAME, CHAN_ADDRESS)

  def connect(self):
    self.api = BitmessageServer()

  def keep_alive(fun):
    def ping_and_reconnect(self, *args, **kwargs):
      try:
        response = self.api.helloWorld('x', 'y')
        assert(response == "x-y")
      except:
        self.connect()
      return fun(self, *args, **kwargs)
    return ping_and_reconnect

  @keep_alive
  def create_random_address(self, label=None):
    if not label:
      label = self.default_address_label
    label_base64 = base64.encodestring(label)
    self.api.createRandomAddress(label_base64)
    self.get_addresses()

  @keep_alive
  def get_addresses(self):
    addresses_json = self.api.listAddresses2()
    logging.debug(addresses_json)
    address_list = json.loads(addresses_json)['addresses']

    self.addresses = \
        [BitmessageAddress(address_dict) for address_dict in address_list]
    self.enabled_addresses = \
        [addr for addr in self.addresses if addr.enabled]

    self.default_address = self.find_default_address()
    if not self.default_address:
      self.create_random_address()

    self.default_address = self.find_default_address()
    # if none - raise exception? it will happen eventually

  @keep_alive
  def find_default_address(self):
    default_address = None
    for address in self.enabled_addresses:
      if address.label == self.default_address_label:
        default_address = address
        break
    return default_address

  @keep_alive
  def update_address_if_empty(self):
    if len(self.addresses) > 0:
      return
    self.create_random_address()

  @keep_alive
  def send_message(self, address, subject, message):
    ack_data = self.api.sendMessage(
                  address, 
                  self.default_address.address, 
                  base64.encodestring(subject),
                  base64.encodestring(message))
    return ack_data

  @keep_alive
  def send_broadcast(self, subject, message):
    ack_data = self.api.sendBroadcast(
                  self.default_address.address,
                  base64.encodestring(subject),
                  base64.encodestring(message))
    return ack_data

  @keep_alive
  def get_inbox(self):
    messages_json = self.api.getAllInboxMessages()
    messages_list = json.loads(messages_json)['inboxMessages']

    messages_inbox = \
        [BitmessageMessage(msg, self.default_address) for msg in messages_list]

    return messages_inbox

  @keep_alive
  def get_unread_messages(self):
    messages = self.get_inbox()
    unread_messages = [msg for msg in messages if not msg.read]
    return unread_messages

  @keep_alive
  def mark_message_as_read(self, msg):
    if isinstance(msg, BitmessageMessage):
      msgid = msg.msgid
    else:
      msgid = msg
    self.api.getInboxMessageByID(msgid, True)

  @keep_alive
  def mark_message_as_unread(self, msg):
    if isinstance(msg, BitmessageMessage):
      msgid = msg.msgid
    else:
      msgid = msg
    self.api.getInboxMessageByID(msgid, False)

  @keep_alive
  def trash_message(self, msgid):
    self.api.trashMessage(msgid)

  @keep_alive
  def delete_address(self, address):
    self.api.deleteAddress(address)

  @keep_alive
  def join_chan(self, name, address):
    name_encoded = base64.encodestring(name)
    try:
      self.api.joinChan(name_encoded, address)
    except ChanAlreadySubscribedException:
      logging.info('subscribed to chan')
