from basehandler import BaseHandler

import json
import logging

from contract_util import get_mark_for_address


class SafeTimelockCreateHandler(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    self.btc = oracle.btc

  def handle_new_block(self, block):
    pass


###
  def handle_request(self, request):
    message = request.message

    if not self.try_prepare_raw_transaction(message):
      logging.debug('transaction looks invalid, ignoring')
      return

    return_address = message['return_address']
    mark = get_mark_for_address(return_address)


    contract_id = self.oracle.btc.add_multisig_address(message['req_sigs'], message['pubkey_list'])

    reply_msg = { 'operation' : 'safe_timelock_created',
        'contract_id' : contract_id,
        'in_reply_to' : message['message_id'] }

    logging.debug('broadcasting reply')
    self.oracle.communication.broadcast("timelock created for %s" % contract_id, json.dumps(reply_msg))

    locktime = int(message['locktime'])

    message['contract_id'] = contract_id

    self.oracle.task_queue.save({
        "operation": 'safe_timelock_create',
        "json_data": json.dumps(message),
        "done": 0,
        "next_check": int(locktime)
    })

  def handle_task(self, task):
    message = json.loads(task['json_data'])
    future_transaction = self.try_prepare_raw_transaction(message)
    assert(future_transaction is not None) # should've been verified gracefully in handle_request

    logging.debug('transaction ready to be signed')

    self.oracle.signer.sign(future_transaction, message['pwtxid'], message['prevtxs'], message['req_sigs'])
