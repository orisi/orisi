from baserequesthandler import BaseRequestHandler
from oracle.oracle_db import UsedInput
from oracle.oracle_protocol import RESPONSE, SUBJECT
from oracle.condition_evaluator.evaluator import Evaluator

import hashlib
import json
import logging

from xmlrpclib import ProtocolError

HEURISTIC_ADD_TIME = 60 * 3

class TransactionVerificationError(Exception):
  pass

class ConditionedTransactionRequestHandler(BaseRequestHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    self.evaluator = Evaluator()

  def inputs_from_same_address(self, prevtxs):
    addresses = self.inputs_addresses(prevtxs)
    if len(addresses) != 1:
      return False
    return True

  def inputs_addresses(self, prevtxs):
    addresses = set()
    for prevtx in prevtxs:
      if not 'redeemScript' in prevtx:
        return False
      script = prevtx['redeemScript']
      address = self.oracle.btc.get_address_from_script(script)
      addresses.add(address)
    return list(addresses)

  def includes_me(self, prevtx):
    for tx in prevtx:
      if not 'redeemScript' in tx:
        return False
      my_turn = self.get_my_turn(tx['redeemScript'])
      if my_turn < 0:
        return False
    return True

  def get_my_turn(self, redeem_script):
    """
    Returns which one my address is in sorted (lexicographically) list of all
    addresses included in redeem_script.
    """
    addresses = sorted(self.oracle.btc.addresses_for_redeem(redeem_script))
    for idx, addr in enumerate(addresses):
      if self.oracle.btc.address_is_mine(addr):
        return idx
    return -1

  def verify_transaction(self, tx):
    transaction = tx['raw_transaction']
    prevtx = tx['prevtx']

    if not self.oracle.btc.is_valid_transaction(transaction):
      logging.debug("transaction invalid")
      raise TransactionVerificationError()

    if not self.inputs_from_same_address(prevtx):
      logging.debug("all inputs should go from the same multisig address")
      raise TransactionVerificationError()

    if not self.includes_me(prevtx):
      logging.debug("transaction does not include me")
      raise TransactionVerificationError()

    if not self.oracle.btc.transaction_contains_org_fee(transaction):
      logging.debug("org fee not found")
      raise TransactionVerificationError()

    if not self.oracle.btc.transaction_contains_oracle_fee(transaction):
      logging.debug("oracle fee not found")
      raise TransactionVerificationError()

    if self.oracle.btc.transaction_already_signed(transaction, prevtx):
      logging.debug("transaction already signed")
      raise TransactionVerificationError()

  def get_inputs_outputs(self, transactions):
    all_inputs = set()
    all_outputs = []

    for transaction in transactions:
      inputs, output = self.oracle.btc.get_inputs_outputs(transaction)
      for i in inputs:
          all_inputs.add(i)
      all_outputs.extend(output)

    all_inputs = sorted(list(all_inputs))
    all_outputs = sorted(all_outputs)
    return (all_inputs, all_outputs)

  def get_request_hash(self, request):
    raw_transactions = [tx['raw_transaction'] for tx in request['transactions']]
    inputs, outputs = self.get_inputs_outputs(raw_transactions)
    request_dict= {
        "inputs": inputs,
        "outputs": outputs,
        "locktime": request['locktime'],
        "condition": request['condition']
    }
    return hashlib.sha256(json.dumps(request_dict)).hexdigest()

  def add_transaction(self, message):
    body = json.loads(message.message)

    pubkey_list = body['pubkey_json']
    try:
      req_sigs = int(body['req_sigs'])
    except ValueError:
      logging.debug("req_sigs must be a number")
      return

    try:
      locktime = int(body['locktime'])
    except ValueError:
      logging.debug("locktime must be a number")
      return

    condition = body['condition']
    # Future reference - add parsing condition. Now assumed true
    if not self.evaluator.valid(condition):
      logging.debug("condition invalid")
      return

    try:
      self.oracle.btc.add_multisig_address(req_sigs, pubkey_list)
    except ProtocolError:
      logging.debug("cant add multisig address")
      return

    transactions = body['transactions']
    for tx in transactions:
      try:
        self.verify_transaction(tx)
      except TransactionVerificationError:
        return

    raw_transactions = [tx['raw_transaction'] for tx in transactions]
    all_inputs, all_outputs = self.get_inputs_outputs(raw_transactions)

    rq_hash = self.get_request_hash(body)

    used_input_db = UsedInput(self.oracle.db)
    for i in all_inputs:
      used_input = used_input_db.get_input(i)
      if used_input:
        if used_input["json_out"] != rq_hash:
          self.oracle.communication.broadcast(
              SUBJECT.ADDRESS_DUPLICATE,
              RESPONSE.ADDRESS_DUPLICATE)
          return
    for i in all_inputs:
      used_input_db.save({
          'input_hash': i,
          'json_out': rq_hash
      })

    all_turns = []
    for transaction in transactions:
      prevtx = transaction['prevtx']
      turns = [self.get_my_turn(tx['redeemScript']) for tx in prevtx if 'redeemScript' in tx]
      my_turn = max(turns)
      all_turns.append(my_turn)

    my_turn = max(all_turns)
    add_time = my_turn * HEURISTIC_ADD_TIME

    self.oracle.task_queue.save({
        "operation": 'conditioned_transaction',
        "json_data": message.message,
        "filter_field": 'rqhs:{}'.format(rq_hash),
        "done": 0,
        "next_check": locktime + add_time
    })

  def handle_request(self, request):
    self.add_transaction(request)

