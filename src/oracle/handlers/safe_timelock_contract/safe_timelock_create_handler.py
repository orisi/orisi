from basehandler import BaseHandler

import json
import cjson
import logging
import time
import datetime

from contract_util import get_mark_for_address
from oracle_db import KeyValue

TIME_FOR_TRANSACTION = 30
TIME_FOR_CONFIRMATION = 13
NUMBER_OF_CONFIRMATIONS = 3

class SafeTimelockCreateHandler(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    self.btc = oracle.btc
    self.kv = KeyValue(self.oracle.db)

  def mark_unavailable(self, mark, addr):
    mark_data = self.kv.get_by_section_key('mark_available', '{}#{}'.format(mark, addr))
    if not mark_data:
      return False

    available = mark_data['available']
    return available

  def claim_mark(self, mark, addr, return_address, locktime):
    mark_data = self.kv.get_by_section_key('mark_available', '{}#{}'.format(mark, addr))
    if not mark_data:
      self.kv.store('mark_available', '{}#{}'.format(mark, addr), {'available':True})

    self.kv.store('mark_available', '{}#{}'.format(mark, addr), {
      'available': False,
      'return_address': return_address,
      'ts': int(time.mktime(datetime.datetime.utcnow().timetuple()).total_seconds()),
      'locktime': locktime,
    })

  def extend_observed_addresses(self, address):
    observed_addresses = self.kv.get_by_section_key('safe_timelock', 'addresses')
    if not observed_addresses:
      self.kv.store('safe_timelock', 'addresses', {'addresses':[]})

    observed_addresses = self.kv.get_by_section_key('safe_timelock', 'addresses')
    observed_addresses = observed_addresses['addresses']
    if address in observed_addresses:
      return

    observed_addresses.append(address)
    self.kv.update('safe_timelock', 'addresses', {'addresses':observed_addresses})

  def handle_request(self, request):
    message = request.message

    return_address = message['return_address']
    mark = get_mark_for_address(return_address)
    address_to_pay_on = self.oracle.btc.add_multisig_address(message['req_sigs'], message['pubkey_list'])

    self.extend_observed_addresses(address_to_pay_on)

    locktime = int(message['locktime'])

    if self.mark_unavailable(mark, address_to_pay_on, return_address):
      reply_msg = {
        'operation': 'safe_timelock_error',
        'in_reply_to': message['message_id'],
        'comment': 'mark for this address is currently unavailable - please try again in several minutes'
      }
      self.oracle.communication.broadcast("safe timelock error", json.dumps(reply_msg))
      return

    # For now oracles are running single-thread so there is no race condition
    self.claim_mark(mark, address_to_pay_on, return_address, locktime)

    reply_msg = { 'operation' : 'safe_timelock_created',
        'contract_id' : address_to_pay_on,
        'comment': 'mark claimed, you have {} minutes to send cash to address {}'.format(TIME_FOR_TRANSACTION, address_to_pay_on),
        'in_reply_to' : message['message_id'] }

    self.oracle.communication.broadcast("timelock created for %s" % address_to_pay_on, json.dumps(reply_msg))

    message['contract_id'] = address_to_pay_on

    now = datetime.datetime.utcnow()
    seconds_now = time.mktime(now.timetuple()).total_seconds()
    release_time = seconds_now + TIME_FOR_TRANSACTION + NUMBER_OF_CONFIRMATIONS * TIME_FOR_CONFIRMATION

    self.oracle.task_queue.save({
        "operation": 'timelock_mark_release',
        "json_data": json.dumps({'mark': mark, 'address': address_to_pay_on}),
        "done": 0,
        "next_check": release_time
    })

  def handle_task(self, task):
    message = cjson.decode(task['json_data'])

    future_transaction = self.try_prepare_raw_transaction(message)
    assert(future_transaction is not None) # should've been verified gracefully in handle_request

    logging.debug('transaction ready to be signed')

    self.oracle.signer.sign(future_transaction, message['pwtxid'], message['prevtxs'], message['req_sigs'])
