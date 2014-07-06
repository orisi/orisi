from basehandler import BaseHandler
from oracle.oracle_db import SignedTransaction, HandledTransaction, UsedInput
from oracle.handlers import SUBJECT, RESPONSE

import hashlib
import json
import logging
import re

from xmlrpclib import ProtocolError

HEURISTIC_ADD_TIME = 60 * 3

class TransactionVerificationError(Exception):
  pass

class ConditionedTransactionHandler(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle

  def handle_task(self, task):
    body = json.loads(task['json_data'])
    tx = body['transaction']

    signed_transaction = self.oracle.btc.sign_transaction(tx['raw_transaction'], tx['prevtx'])
    body['transaction']['raw_transaction'] = signed_transaction

    SignedTransaction(self.oracle.db).save({
        "hex_transaction": signed_transaction,
        "prevtx":json.dumps(tx['prevtx'])})

    self.oracle.communication.broadcast_signed_transaction(json.dumps(body))
    self.oracle.task_queue.done(task)

  def valid_task(self, task):
    match = re.match(r'^rqhs:(.*)', task['filter_field'])
    if not match:
      return False
    rqhs = match.group(1)

    tx = json.loads(task['json_data'])['transaction']

    raw_transaction = tx['raw_transaction']
    prevtx = tx['prevtx']
    
    signatures_for_this_tx = self.oracle.btc.signatures_number(
        raw_transaction,
        prevtx)

    # If there is already a transaction that has MORE signatures than what we
    # have here - then ignore all tasks
    signs_for_transaction = HandledTransaction(self.oracle.db).signs_for_transaction(rqhs)

    if signs_for_transaction > signatures_for_this_tx:
      valid_task = False
    else:
      valid_task = True

    HandledTransaction(self.oracle.db).update_tx(rqhs, signatures_for_this_tx)
    return valid_task


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

    if len(self.inputs_addresses(prevtx))>1:
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

  def get_request_hash(self, request):
    raw_transaction = request['transaction']['raw_transaction']
    inputs, outputs = self.oracle.get_inputs_outputs([ raw_transaction ])
    request_dict= {
        "inputs": inputs,
        "outputs": outputs,
        "locktime": request['locktime'],
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

    try:
      self.oracle.btc.add_multisig_address(req_sigs, pubkey_list)
    except ProtocolError:
      logging.debug("cant add multisig address")
      return



    tx = body['transaction']
    try:
      self.verify_transaction(tx)
    except TransactionVerificationError:
      return

    raw_transaction = tx['raw_transaction']
    all_inputs, all_outputs = self.oracle.get_inputs_outputs([raw_transaction])

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

    prevtx = tx['prevtx']
    turns = [self.get_my_turn(ptx['redeemScript']) for ptx in prevtx if 'redeemScript' in tx]
    
    my_turn = max(turns)
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
