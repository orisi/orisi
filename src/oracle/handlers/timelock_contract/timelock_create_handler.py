from basehandler import BaseHandler
from password_db import LockedPasswordTransaction

import json
import logging

from decimal import Decimal, getcontext

class ConditionedTransactionHandler(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    self.btc = oracle.btc
    getcontext().prec=8


  def try_prepare_transaction(self, message):
    inputs = []
    for tx in message['prevtx']:
      inputs.append({'txid': tx['txid'], 'vout': tx['vout']})

    cash_back = Decimal(message['sum_amount']) - Decimal(message['miners_fee'])

    outputs = message['oracle_fees']

    for oracle, fee in outputs.iteritems():
      cash_back -= Decimal(fee)

      if self.oracle.is_fee_sufficient(oracle, fee):
        has_my_fee = True

    if not has_my_fee:
      logging.debug("No fee for this oracle, skipping")
      return None

    if cash_back < 0:
      logging.debug("BTC amount not high enough to cover expenses")
      return None

    outputs[ message['return_address'] ] = cash_back

    for address, value in outputs.iteritems():
      # My heart bleeds when I write it
      # but btc expects float as input for the currency amount
      outputs[address] = float(value)

    transaction = self.btc.create_multisig_transaction(inputs, outputs)
    return transaction


  def handle_request(self, request):
    message = json.loads(request.message)

    if not self.try_prepare_transaction(request.message):
      logging.debug('transaction looks invalid, ignoring')
      return

    pwtxid = self.oracle.btc.add_multisig_address(message['req_sigs'], message['pubkey_list'])

    if LockedPasswordTransaction(self.oracle.db).get_by_pwtxid(pwtxid):
      logging.debug('pwtxid already in use. did you resend the same request?')
      return


    message['operation'] = 'timelock_created'
    message['pwtxid'] = pwtxid
    logging.debug('broadcasting reply')
    self.oracle.communication.broadcast(message['operation'], json.dumps(message))

    LockedPasswordTransaction(self.oracle.db).save({'pwtxid':pwtxid, 'json_data':json.dumps(message)})

    locktime = int(message['locktime'])

    self.oracle.task_queue.save({
        "operation": 'timelock_create',
        "json_data": request.message,
        "filter_field": 'pwtxid:{}'.format(pwtxid),
        "done": 0,
        "next_check": locktime
    })


  def handle_task(self, task):
    message = json.loads(task['json_data'])
    pwtxid = message['pwtxid']

    locktime = message['locktime']
    future_transaction = self.try_prepare_transaction(message)

    future_hash = self.get_raw_tx_hash(future_transaction, locktime)

    if len(self.oracle.task_queue.get_by_filter('rqhs:{}'.format(future_hash))) > 0:
      logging.info("transaction already pushed")
      return

    signed_transaction = self.btc.sign_transaction(future_transaction, message['prevtx'])

    # Prepare request corresponding with protocol
    request = {
        "transactions": [
            {"raw_transaction":signed_transaction, "prevtx": message['prevtx']},],
        "locktime": message['locktime'],
        "condition": "True",
        "pubkey_list": message['pubkey_list'],
        "req_sigs": message['req_sigs'],
        "operation": 'conditioned_transaction'
    }
    request = json.dumps(request)
    self.oracle.communication.broadcast('conditioned_transaction', request)
    self.oracle.task_queue.done(task)

