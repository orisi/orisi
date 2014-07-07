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


  def input_addresses(self, prevtxs):
    addresses = set()
    for prevtx in prevtxs:
      if not 'redeemScript' in prevtx:
        return False
      script = prevtx['redeemScript']
      address = self.btc.decode_script(script)['p2sh']
      addresses.add(address)
    return list(addresses)

  def try_prepare_transaction(self, message):
    inputs = []
    for tx in message['prevtxs']:
      inputs.append({'txid': tx['txid'], 'vout': tx['vout']})

    if len(self.input_addresses(message['prevtxs']))>1:
      logging.debug("all inputs should come from the same multisig address")
      return False

    cash_back = Decimal(message['sum_amount']) - Decimal(message['miners_fee'])

    outputs = message['outputs']

    for oracle, fee in outputs.iteritems():
      cash_back -= Decimal(fee)

      if self.oracle.is_fee_sufficient(oracle, fee):
        has_my_fee = True

    if not has_my_fee:
      logging.debug("no fee for this oracle, skipping")
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

    if not self.try_prepare_transaction(message):
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

    self.oracle.task_queue.save({
        "operation": 'timelock_create',
        "json_data": request.message,
        "filter_field": 'pwtxid:{}'.format(pwtxid),
        "done": 0,
        "next_check": locktime
    })


  def handle_task(self, task):
    message = json.loads(task['json_data'])

    future_transaction = self.try_prepare_transaction(message)

    logging.debug('transaction ready to be signed')

    self.oracle.signer.sign(future_transaction, message['prevtxs'], message['req_sigs'])