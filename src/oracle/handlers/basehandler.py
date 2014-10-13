
import json
import hashlib

import logging

from decimal import Decimal, getcontext

SATOSHI = 0.00000001

class BaseHandler:
  def __init__(self, oracle):
    self.oracle = oracle
    self.btc = oracle.btc
    getcontext().prec=8

  def handle_request(self, request):
    raise NotImplementedError()

  def handle_task(self, task):
    raise NotImplementedError()

  def get_observed_addresses(self):
    """
    Returns list of addresses we're observing and waiting for transactions on that addresses
    """
    return []

  def handle_new_transactions(self, transactions):
    pass

  def valid_task(self, task):
  	return True

  def get_tx_hash(self, tx):
    inputs, outputs = self.btc.get_inputs_outputs(tx)
    request_dict= {
        "inputs": inputs,
        "outputs": outputs,
    }

    return hashlib.sha256(json.dumps(request_dict)).hexdigest()

  def input_addresses(self, prevtxs):
    addresses = set()
    for prevtx in prevtxs:
      if not 'redeemScript' in prevtx:
        return False
      script = prevtx['redeemScript']
      address = self.btc.decode_script(script)['p2sh']
      addresses.add(address)
    return list(addresses)

  def try_prepare_raw_transaction_full_node(self, message):
    value = message['value']
    return_address = message['return_address']
    txid = message['txid']
    n = message['n']
    oracle_fees = message['oracle_fees']

    outputs = {}

    left_cash = value - (SATOSHI * message['miners_fee_satoshi'])

    has_my_fee = False
    for oracle, fee in oracle_fees.iteritems():
      outputs[oracle] = fee
      left_cash -= fee

      if self.oracle.is_fee_sufficient(oracle, fee):
        has_my_fee = True

    if not has_my_fee:
      logging.debug("no fee for this oracle, skipping")
      return None

    if left_cash < 0:
      logging.debug("BTC amount not high enough to cover expenses")
      return None

    outputs[return_address] = left_cash
    inputs = [(txid, n)]

    transaction = self.btc.create_raw_transaction(inputs, outputs)
    return transaction

  def try_prepare_raw_transaction(self, message):
    inputs = []

    logging.debug(message)

    for tx in message['prevtxs']:
      inputs.append({'txid': tx['txid'], 'vout': tx['vout']})

    if len(self.input_addresses(message['prevtxs']))>1:
      logging.debug("all inputs should come from the same multisig address")
      return False

    cash_back = Decimal(Decimal(SATOSHI) * (message['sum_satoshi'] - message['miners_fee_satoshi']))

    logging.debug(cash_back)

    outputs = {}#message['outputs']

    has_my_fee = False
    for oracle, fee in message['outputs'].iteritems(): #outputs.iteritems():
      outputs[oracle] = fee
      cash_back -= Decimal(fee)

      if self.oracle.is_fee_sufficient(oracle, fee):
        has_my_fee = True

    if not has_my_fee:
      logging.debug("no fee for this oracle, skipping")
      return None

    if cash_back < 0:
      logging.debug("BTC amount not high enough to cover expenses")
      return None

    outputs[ message['return_address'] ] = float(cash_back)

    logging.debug("outputs2: %r" % outputs)

    for address in outputs:
      # My heart bleeds when I write it
      # but btc expects float as input for the currency amount
      outputs[address] = float(outputs[address])


    logging.debug(outputs)

    transaction = self.btc.create_raw_transaction(inputs, outputs)
    return transaction
