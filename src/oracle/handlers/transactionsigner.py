from basehandler import BaseHandler
from oracle.oracle_db import SignedTransaction, HandledTransaction, UsedInput

import hashlib
import json
import logging
import re

from xmlrpclib import ProtocolError

HEURISTIC_ADD_TIME = 60 * 3

class TransactionVerificationError(Exception):
  pass

class TransactionSigner(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    self.btc = oracle.btc

  def handle_task(self, task):
    body = json.loads(task['json_data'])
    tx = body['transaction']

    signed_transaction = self.btc.sign_transaction(tx['raw_transaction'], tx['prevtx'])
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
    
    signatures_for_this_tx = self.btc.signatures_number(
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
    addresses = sorted(self.btc.decode_script(redeem_script)['addresses'])
    for idx, addr in enumerate(addresses):
      if self.btc.address_is_mine(addr):
        return idx
    return -1

  def handle_request(self, request):
    body = json.loads(request.message)

    pubkey_list = body['pubkey_list']
    req_sigs = int(body['req_sigs'])
    self.btc.add_multisig_address(req_sigs, pubkey_list)
    
    tx = body['transaction']

    # validity of the transaciton should be checked by handlers
    assert( self.is_proper_transaction(tx) )

    raw_transaction = tx['raw_transaction']
    all_inputs, all_outputs = self.btc.get_inputs_outputs(raw_transaction)

    rq_hash = self.get_raw_tx_hash(raw_transaction, body['locktime'])

    used_input_db = UsedInput(self.oracle.db)
    for i in all_inputs:
      used_input = used_input_db.get_input(i)
      if used_input:
        if used_input["json_out"] != rq_hash:
          self.oracle.communication.broadcast(
              'AddressDuplicate',
              'this multisig address was already used')
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
        "json_data": request.message,
        "filter_field": 'rqhs:{}'.format(rq_hash),
        "done": 0,
        "next_check": locktime + add_time
    })
