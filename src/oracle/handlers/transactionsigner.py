from basehandler import BaseHandler
from oracle.oracle_db import KeyValue

import json
import logging
import time

TURN_LENGTH_TIME = 60 * 3

class TransactionVerificationError(Exception):
  pass

class TransactionSigner(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    self.btc = oracle.btc
    self.kv = KeyValue(self.oracle.db)


  def includes_me(self, prevtx):
    for tx in prevtx:
      if not 'redeemScript' in tx:
        return False
      my_turn = self.get_my_turn(tx['redeemScript'])
      if my_turn < 0:
        return False
    return True

  def get_my_turn(self, redeem_script):
    addresses = sorted(self.btc.decode_script(redeem_script)['addresses'])
    for idx, addr in enumerate(addresses):
      if self.btc.address_is_mine(addr):
        return idx
    return -1


  def is_proper_transaction(self, tx):

    if not self.oracle.btc.is_valid_transaction(tx):
      logging.debug("transaction invalid")
      return False

    inputs, outputs = self.btc.get_inputs_outputs(tx)

    if not self.includes_me(inputs):
      logging.debug("transaction does not include me")
      return False

    if self.oracle.btc.transaction_already_signed(tx, inputs):
      logging.debug("transaction already signed")
      return False

    return True


  def sign(self, tx, inputs, req_sigs):

    tx_inputs, tx_outputs = self.btc.get_inputs_outputs(tx)

    #todo: shouldn't all the input scripts be guaranteed to be exactly the same by now?
    turns = [self.get_my_turn(vin['redeemScript']) for vin in inputs if 'redeemScript' in vin]

    my_turn = max(turns)
    add_time = my_turn * TURN_LENGTH_TIME

    rq_hash = self.get_tx_hash(tx)

    self.kv.store( 'signable', rq_hash, { 'inputs':inputs, 'sigs_so_far':0, 'req_sigs': req_sigs } ) # TODO: add min sigs

    self.oracle.task_queue.save({
        "operation": 'sign',
        "json_data": {"transaction": tx},
        "next_check": time.time() + add_time,
        "done": 0, # to be removed TODO
        "filter_field": 'rqhash:{}'.format(rq_hash) # to be removed TODO
    })

  def sign_now(self, tx):
    assert( self.is_proper_transaction(tx) )

    inputs, outputs = self.btc.get_inputs_outputs(tx)

    rq_hash = self.get_tx_hash(tx)

    rq_data = self.kv.get_by_section_key('signable', rq_hash)
    if rq_data is None:
      logging.debug("not scheduled to sign this")
      return

    inputs = rq_data['inputs']
    sigs_so_far = rq_data['sigs_so_far']
    req_sigs = rq_data['req_sigs']

    tx_sigs_count = self.btc.signatures_number(
        tx,
        inputs)

    if sigs_so_far >= tx_sigs_count: # or > not >=? TODO
      logging.debug('already signed a transaction with more sigs')
      return

    if tx_sigs_count >= req_sigs:
      logging.debug('already signed with enough keys')
      return

    signed_transaction = self.btc.sign_transaction(tx, inputs)
    body = { 'transaction': signed_transaction }
    self.oracle.communication.broadcast('sign' if tx_sigs_count else 'final-sign', body)

    rq_data['sigs_so_far'] += 1
    self.kv.update('signable', rq_hash, rq_data)

  def handle_request(self, request):

    body = json.loads(request.message)
    tx = body['transaction']

    self.sign_now(tx)

  def handle_task(self, task): 
    self.oracle.task_queue.done(task)
    message = json.loads(task['json_data'])
    tx = message['transaction']

    rq_hash = self.get_tx_hash(tx)

    rq_data = self.kv.get_by_section_key('signable', rq_hash)
    assert(rq_data is not None)
 
    if rq_data['sigs_so_far'] > 0:
      logging.debug('I already signed more popular txs')
      return

    self.sign_now(tx)
