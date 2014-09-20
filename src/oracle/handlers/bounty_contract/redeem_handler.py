from basehandler import BaseHandler

import json
import cjson
import logging
from oracle.oracle_db import KeyValue
from random import randrange
from Crypto.Hash import SHA512

class BountyRedeemHandler(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    self.btc = oracle.btc
    self.kv = KeyValue(self.oracle.db)

  def handle_request(self, request):
    body = request.message

    return_address = body['return_address']
    password = body['password']
    bounty_name = body['bounty_name']

    bounty_hash = self.kv.get_by_section_key('bounty_name', bounty_name)
    if not bounty_hash:
      logging.info('transaction unknown')
      return

    password_hash = bounty_hash['password_hash']

    bounty_transactions = self.kv.get_by_section_key('bounty_transactions', password_hash)
    if not bounty_transactions:
      logging.info('transaction unknown')
      return

    new_hash = SHA512.new()
    new_hash.update(password)
    new_hash = new_hash.hexdigest()

    if new_hash != password_hash:
      logging.info('guess incorrect {}'.format(password))
      return

    logging.info("guess correct")

    for bounty_transaction in bounty_transactions["entries"]:
      self.send_to_winner(bounty_transaction, return_address)

    self.kv.update('bounty_transactions', password_hash, {"entries": []})


  def send_to_winner(self, message, return_address):
    txid = message['txid']
    n = message['n']
    redeemScript = self.kv.get_by_section_key('bounty_redeem', message['address'])['redeem']
    tx = self.btc.get_raw_transaction(txid)
    transaction = self.btc.decode_raw_transaction(tx)
    vout = None
    for v in transaction['vout']:
      if v['n'] == n:
        vout = v
        break

    if not vout:
      logging.info("missing vout for txid {} n {}".format(txid, n))
      return

    sum_satoshi = int(round(vout['value'] * 100000000))
    message['sum_satoshi'] = sum_satoshi

    scriptPubKey = vout['scriptPubKey']['hex']

    prevtx = {
        'txid': txid,
        'vout': n,
        'redeemScript': redeemScript,
        'scriptPubKey': scriptPubKey
    }
    prevtxs = [prevtx,]
    message['prevtxs'] = prevtxs

    message['outputs'] = message['oracle_fees']

    future_transaction = self.try_prepare_raw_transaction(message)
    if not future_transaction:
      return
    logging.info(future_transaction)

    try:
      pwtxid = self.get_tx_hash(future_transaction)
    except:
      logging.error("Failed to create tx hash")
      return

    assert(future_transaction is not None) # should've been verified gracefully in handle_request

    self.oracle.signer.sign(future_transaction, pwtxid, prevtxs, message['req_sigs'])

    info_msg = {
      'operation': 'bounty_won_signed',
      'in_reply_to': message['message_id'],
      'message_id': "%s-%s" % ("bounty_signature", str(randrange(1000000000,9000000000))),
      'contract_id' : "{}#{}".format(message['address'], message['mark']),
    }

    self.oracle.broadcast_with_fastcast(json.dumps(info_msg))


  def handle_task(self, task):
    message = cjson.decode(task['json_data'])

    txid = message['txid']
    n = message['n']
    redeemScript = self.kv.get_by_section_key('bounty_redeem', message['address'])['redeem']
    tx = self.btc.get_raw_transaction(txid)
    transaction = self.btc.decode_raw_transaction(tx)
    vout = None
    for v in transaction['vout']:
      if v['n'] == n:
        vout = v
        break

    if not vout:
      logging.info("missing vout for txid {} n {}".format(txid, n))
      return

    sum_satoshi = int(round(vout['value'] * 100000000))
    message['sum_satoshi'] = sum_satoshi

    scriptPubKey = vout['scriptPubKey']['hex']

    prevtx = {
        'txid': txid,
        'vout': n,
        'redeemScript': redeemScript,
        'scriptPubKey': scriptPubKey
    }
    prevtxs = [prevtx,]
    message['prevtxs'] = prevtxs

    message['outputs'] = message['oracle_fees']

    future_transaction = self.try_prepare_raw_transaction(message)
    if not future_transaction:
      return
    logging.info(future_transaction)

    try:
      pwtxid = self.get_tx_hash(future_transaction)
    except:
      logging.error("Failed to create tx hash")
      return

    assert(future_transaction is not None) # should've been verified gracefully in handle_request

    self.oracle.signer.sign(future_transaction, pwtxid, prevtxs, message['req_sigs'])

    info_msg = {
      'operation': 'bounty_signed',
      'in_reply_to': message['message_id'],
      'message_id': "%s-%s" % ("bounty_signature", str(randrange(1000000000,9000000000))),
      'contract_id' : "{}#{}".format(message['address'], message['mark']),
    }

    self.oracle.broadcast_with_fastcast(json.dumps(info_msg))
