from basehandler import BaseHandler
from password_db import LockedPasswordTransaction

import json
import logging
import datetime


class ConditionedTransactionHandler(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    self.btc = oracle.btc


  def handle_request(self, request):
    message = request.message

    if not self.try_prepare_raw_transaction(message):
      logging.debug('transaction looks invalid, ignoring')
      return

    pwtxid = self.oracle.btc.add_multisig_address(message['req_sigs'], message['pubkey_list'])

    if LockedPasswordTransaction(self.oracle.db).get_by_pwtxid(pwtxid):
      logging.debug('pwtxid/multisig address already in use. did you resend the same request?')
      return

    reply_msg = { 'operation' : 'timelock_created',
        'pwtxid' : pwtxid,
        'in_reply_to' : message['message_id'] }

    logging.debug('broadcasting reply')
    self.oracle.communication.broadcast(reply_msg['operation'], json.dumps(reply_msg))

    LockedPasswordTransaction(self.oracle.db).save({'pwtxid':pwtxid, 'json_data':json.dumps(message)})

    locktime = int(message['locktime'])

    logging.debug("awaiting %r" % datetime.datetime.fromtimestamp(locktime).strftime('%Y-%m-%d %H:%M:%S'))

    self.oracle.task_queue.save({
        "operation": 'timelock_create',
        "json_data": message,
        "done": 0,
        "next_check": locktime
    })


  def handle_task(self, task):

    message = json.loads(task['json_data'])
    future_transaction = self.try_prepare_raw_transaction(message)
    assert(future_transaction is not None) # should've been verified gracefully in handle_request

    logging.debug('transaction ready to be signed')

    self.oracle.signer.sign(future_transaction, message['prevtxs'], message['req_sigs'])