from basehandler import BaseHandler
from password_db import LockedPasswordTransaction
from util import Util

import hashlib
import json
import logging

from decimal import Decimal, getcontext

KEY_SIZE = 4096
HEURISTIC_ADD_TIME = 60 * 3

# 15 minutes just to be sure no one claimed it
SAFETY_TIME = 15 * 60

class ConditionedTransactionHandler(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    getcontext().prec=8

  def get_unique_id(self, message):
    return hashlib.sha256(message).hexdigest()


  def handle_request(self, request):
    message = json.loads(request.message)

    sum_amount = Decimal(message['sum_amount'])
    oracle_fees = message['oracle_fees']
    miners_fee = Decimal(message['miners_fee'])

    final_amount = sum_amount - miners_fee


    has_my_fee = False
    for oracle, fee in oracle_fees.iteritems():
      final_amount -= Decimal(fee)

      if self.oracle.is_fee_sufficient(oracle, fee):
        has_my_fee = True

    if not has_my_fee:
      logging.debug("There is no fee for oracle, skipping")
      return

    pwtxid = self.oracle.btc.add_multisig_address(message['req_sigs'], message['pubkey_list'])

    if LockedPasswordTransaction(self.oracle.db).get_by_pwtxid(pwtxid):
      logging.info('pwtxid already in use. did you resend the same request?')
      return

    pub_key = self.get_public_key(pwtxid)
    message['rsa_pubkey'] = json.loads(pub_key)
    message['operation'] = 'new_bounty'
    message['pwtxid'] = pwtxid

    locktime = int(message['locktime'])

    LockedPasswordTransaction(self.oracle.db).save({'pwtxid':pwtxid, 'json_data':json.dumps(message)})
    logging.debug('broadcasting reply')
    self.oracle.communication.broadcast(message['operation'], json.dumps(message))
    self.oracle.task_queue.save({
        "operation": 'password_transaction',
        "json_data": request.message,
        "filter_field": 'pwtxid:{}'.format(pwtxid),
        "done": 0,
        "next_check": locktime
    })


  def handle_task(self, task):
    message = json.loads(task['json_data'])
    pwtxid = self.get_unique_id(task['json_data'])

    transaction = LockedPasswordTransaction(self.oracle.db).get_by_pwtxid(pwtxid)
    if not transaction:
      # This should be weird
      logging.error('task doesn\'t apply to any transaction')
      return

    if transaction['done']:
      logging.info('transaction done')
      return

    prevtx = message['prevtx']
    locktime = message['locktime']
    outputs = message['oracle_fees']
    sum_amount = Decimal(message['sum_amount'])
    miners_fee = Decimal(message['miners_fee'])
    available_amount = sum_amount - miners_fee
    return_address = message['return_address']
    future_transaction = Util.create_future_transaction(self.oracle.btc, prevtx, outputs, available_amount, return_address, locktime)

    future_hash = self.get_raw_tx_hash(future_transaction, locktime)

    if len(self.oracle.task_queue.get_by_filter('rqhs:{}'.format(future_hash))) > 0:
      logging.info("transaction already pushed")
      return

    signed_transaction = self.oracle.btc.sign_transaction(future_transaction, prevtx)

    # Prepare request corresponding with protocol
    request = {
        "transactions": [
            {"raw_transaction":signed_transaction, "prevtx": prevtx},],
        "locktime": message['locktime'],
        "condition": "True",
        "pubkey_list": message['pubkey_list'],
        "req_sigs": message['req_sigs'],
        "operation": 'conditioned_transaction'
    }
    request = json.dumps(request)
    self.oracle.communication.broadcast('conditioned_transaction', request)
    LockedPasswordTransaction(self.oracle.db).mark_as_done(pwtxid)
    self.oracle.task_queue.done(task)

