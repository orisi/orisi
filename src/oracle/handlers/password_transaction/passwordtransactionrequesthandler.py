from basehandler import BaseHandler
from password_db import LockedPasswordTransaction, RSAKeyPairs

import hashlib
import json
import logging

from Crypto.PublicKey import RSA
from Crypto import Random
from decimal import Decimal, getcontext

BOUNTY_SUBJECT = "New bounty available!"
KEY_SIZE = 4096
HEURISTIC_ADD_TIME = 60*3

class PasswordTransactionRequestHandler(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    getcontext().prec=8

  def get_unique_id(self, message):
    return hashlib.sha256(message).hexdigest()

  def get_public_key(self, pwtxid):
    random_generator = Random.new().read
    new_keypair = RSA.generate(KEY_SIZE, random_generator)
    public_key = json.dumps({'n':new_keypair.n, 'e':new_keypair.e})
    whole_key_serialized = json.dumps({
        'n':new_keypair.n,
        'e':new_keypair.e,
        'd':new_keypair.d,
        'p':new_keypair.p,
        'q':new_keypair.q,
        'u':new_keypair.u})
    RSAKeyPairs(self.oracle.db).save({
        'pwtxid': pwtxid,
        'public': public_key,
        'whole': whole_key_serialized})
    return public_key

  def construct_key_from_data(self, rsa_data):
    k = json.loads(rsa_data['whole'])
    key = RSA.construct((
        long(k['n']),
        long(k['e']),
        long(k['d']),
        long(k['p']),
        long(k['q']),
        long(k['u'])))
    return key

  def get_my_turn(self, oracle_fees):
    addresses = sorted([k for k,_ in oracle_fees.iteritems()])
    for idx, addr in enumerate(addresses):
      if self.oracle.btc.address_is_mine(addr):
        return idx

  def handle_request(self, request):
    message = json.loads(request.message)

    sum_amount = Decimal(message['sum_amount'])
    oracle_fees = message['oracle_fees']
    miners_fee = Decimal(message['miners_fee'])

    final_amount = sum_amount - miners_fee
    for oracle, fee in oracle_fees.iteritems():
      final_amount -= Decimal(fee)

    oracle_fee = sum([self.oracle.is_fee_sufficient(oracle, fee) for (oracle, fee) in list(oracle_fees.iteritems())])
    if not oracle_fee > 0:
      logging.debug("There is no fee for oracle, skipping")
      return
    pwtxid = self.get_unique_id(request.message)

    pub_key = self.get_public_key(pwtxid)
    message['rsa_pubkey'] = pub_key

    locktime = int(message['locktime'])

    my_turn = self.get_my_turn(oracle_fees)
    add_time = my_turn * HEURISTIC_ADD_TIME

    LockedPasswordTransaction(self.oracle.db).save({'pwtxid':pwtxid, 'json_data':json.dumps(message)})
    self.oracle.communication.broadcast(BOUNTY_SUBJECT, message)
    self.oracle.task_queue.save({
        "operation": 'password_transaction',
        "json_data": request.message,
        "filter_field": 'pwtxid:{}'.format(pwtxid),
        "done": 0,
        "next_check": locktime + add_time
    })

  def handle_task(self, task):
    pass

  def filter_tasks(self, task):
    return [task]
