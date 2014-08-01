from basehandler import BaseHandler

import json
import logging
import time
import datetime

from contract_util import get_mark_for_address

TIME_FOR_TRANSACTION = 30
TIME_FOR_CONFIRMATION = 13
NUMBER_OF_CONFIRMATIONS = 3

class SafeTimelockCreateHandler(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    self.btc = oracle.btc

  def handle_new_block(self, block):
    pass

  def mark_unavailable(self, mark):
    raise NotImplementedError

  def claim_mark(self, mark, return_address, locktime):
    raise NotImplementedError()

  def handle_request(self, request):
    message = request.message

    return_address = message['return_address']
    mark = get_mark_for_address(return_address)

    locktime = int(message['locktime'])

    if self.mark_unavailable(mark):
      reply_msg = {
        'operation': 'safe_timelock_error',
        'in_reply_to': message['message_id'],
        'comment': 'mark for this address is currently unavailable - please try again in several minutes'
      }
      self.oracle.communication.broadcast("safe timelock error", json.dumps(reply_msg))
      return

    # For now oracles are running single-thread so there is no race condition
    self.claim_mark(mark, return_address, locktime)

    address_to_pay_on = self.oracle.btc.add_multisig_address(message['req_sigs'], message['pubkey_list'])

    reply_msg = { 'operation' : 'safe_timelock_created',
        'contract_id' : address_to_pay_on,
        'comment': 'mark claimed, you have {} minutes to send cash to address {}'.format(TIME_FOR_TRANSACTION, address_to_pay_on),
        'in_reply_to' : message['message_id'] }

    self.oracle.communication.broadcast("timelock created for %s" % address_to_pay_on, json.dumps(reply_msg))

    message['contract_id'] = address_to_pay_on

    self.oracle.task_queue.save({
        "operation": 'safe_timelock_create',
        "json_data": json.dumps(message),
        "done": 0,
        "next_check": int(locktime)
    })

    now = datetime.datetime.utcnow()
    seconds_now = time.mktime(now.timetuple()).total_seconds()
    release_time = seconds_now + TIME_FOR_TRANSACTION + NUMBER_OF_CONFIRMATIONS * TIME_FOR_CONFIRMATION

    self.oracle.task_queue.save({
        "operation": 'timelock_mark_release',
        "json_data": json.dumps({'mark': mark}),
        "done": 0,
        "next_check": release_time
    })

  def handle_task(self, task):
    message = json.loads(task['json_data'])
    future_transaction = self.try_prepare_raw_transaction(message)
    assert(future_transaction is not None) # should've been verified gracefully in handle_request

    logging.debug('transaction ready to be signed')

    self.oracle.signer.sign(future_transaction, message['pwtxid'], message['prevtxs'], message['req_sigs'])
