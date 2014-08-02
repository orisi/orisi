from basehandler import BaseHandler
from oracle.oracle_db import KeyValue

import json
import logging
import time

from shared.liburl_wrapper import safe_pushtx


TURN_LENGTH_TIME = 60 * 1

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
    # oracles sign transactions based on the order of their signatures

    addresses = sorted(self.btc.decode_script(redeem_script)['addresses'])
    for idx, addr in enumerate(addresses):
      if self.btc.address_is_mine(addr):
        return idx
    return -1


  def is_proper_transaction(self, tx, prevtxs):
    logging.info('testing tx: %r' % tx)
    logging.info('with prevtxs: %r' % prevtxs)

    if not self.oracle.btc.is_valid_transaction(tx):
      logging.debug("transaction invalid")
      return False

    inputs, outputs = self.btc.get_inputs_outputs(tx)

    if not self.includes_me(prevtxs):
      logging.debug("transaction does not include me")
      return False

    if self.oracle.btc.transaction_already_signed(tx, prevtxs):
      logging.debug("transaction already signed")
      return False

    return True


  def sign(self, tx, pwtxid, inputs, req_sigs):
    # sign is being called by external contracts to initiate signing procedure
    # it marks the transaction as being ready to be signed if received from bitmessage
    # and schedules signing -- in case oracles previous in line didn't want to sign it

    logging.debug("tx: %r" % tx)

    tx_inputs, tx_outputs = self.btc.get_inputs_outputs(tx)

    #todo: shouldn't all the input scripts be guaranteed to be exactly the same by now?
    turns = [self.get_my_turn(vin['redeemScript']) for vin in inputs if 'redeemScript' in vin]

    my_turn = max(turns)
    add_time = (my_turn - 1) * TURN_LENGTH_TIME

    rq_hash = self.get_tx_hash(tx)

    try:
      self.kv.store( 'signable', rq_hash, { 'inputs':inputs, 'sigs_so_far':0, 'req_sigs': req_sigs , 'pwtxid' : pwtxid } )
    except:
      logging.warning('duplicate sign task? this try..except should be removed ultimately!')

    self.oracle.task_queue.save({
        "operation": 'sign',
        "json_data": json.dumps({"transaction": tx}),
        "next_check": time.time() + add_time,
        "done": 0,
    })

  def sign_now(self, tx):
    # sign now signs the transaction and broadcasts it over the network

    inputs, outputs = self.btc.get_inputs_outputs(tx)

    rq_hash = self.get_tx_hash(tx)

    rq_data = self.kv.get_by_section_key('signable', rq_hash)
    if rq_data is None:
      logging.debug("not scheduled to sign this")
      return

    inputs = rq_data['inputs']
    sigs_so_far = rq_data['sigs_so_far']
    req_sigs = rq_data['req_sigs']

    assert( self.is_proper_transaction(tx, inputs) )

    tx_sigs_count = self.btc.signatures_count(
        tx,
        inputs)

    logging.debug("sigs count so far: %r; req_sigs: %r" % (tx_sigs_count, req_sigs))

    if sigs_so_far > tx_sigs_count: # or > not >=? TODO
      logging.debug('already signed a transaction with more sigs')
      return

    rq_data['sigs_so_far'] = tx_sigs_count
    self.kv.update('signable', rq_hash, rq_data)
    # ^ let's remember the tx with most sigs that we've seen.

    if tx_sigs_count >= req_sigs:
      logging.debug('already signed with enough keys')
      return

    pwtxid = rq_data['pwtxid']

    signed_transaction = self.btc.sign_transaction(tx, inputs)

    tx_new_sigs_count = self.btc.signatures_count(signed_transaction, inputs)

    if (tx_new_sigs_count == tx_sigs_count):
      logging.debug('failed signing transaction. already signed by me? aborting')
      return

    tx_sigs_count += 1

    body = { 'pwtxid': pwtxid, 'operation':'sign', 'transaction': signed_transaction, 'sigs': tx_sigs_count, 'req_sigs': req_sigs }

    logging.debug('broadcasting: %r' % body)

    subject = ('sign %s' % pwtxid)  if tx_sigs_count < req_sigs else ('final-sign %s' % pwtxid)

    if tx_sigs_count == req_sigs:
      logging.debug('pushing tx to Eligius. you might want to disable this in test systems')
      logging.debug(safe_pushtx(signed_transaction))

    self.oracle.communication.broadcast(subject, json.dumps(body))

    rq_data['sigs_so_far'] = tx_sigs_count
    self.kv.update('signable', rq_hash, rq_data)

  def handle_request(self, request):
    body = request.message
    # if the oracle received a transaction from bitmessage, it attempts to sign it
    # all the validity checks are being handled by sign_now

    tx = body['transaction']

    self.sign_now(tx)

  def handle_task(self, task):
    # handles scheduled signing
    # in a perfect world only the first oracle would have to call this
    # and all the others would sign through handle_request

    self.oracle.task_queue.done(task)
    message = json.loads(task['json_data'])
    tx = message['transaction']

    rq_hash = self.get_tx_hash(tx)

    rq_data = self.kv.get_by_section_key('signable', rq_hash)
    assert(rq_data is not None)

    logging.info("rq_data: %r" % rq_data)

    if rq_data['sigs_so_far'] > 0:
      logging.debug('I already signed more popular txs')
      return

    self.sign_now(tx)
