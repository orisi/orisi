
#### This module doesn't work after the signing procedure refactor. To be done

from basehandler import BaseHandler
from password_db import LockedPasswordTransaction, RSAKeyPairs

import hashlib
import json
import logging

from Crypto.PublicKey import RSA
from Crypto import Random

KEY_SIZE = 4096
HEURISTIC_ADD_TIME = 60 * 3

class BountyCreateHandler(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    self.btc = oracle.btc

  def get_unique_id(self, message):
    return hashlib.sha256(message).hexdigest()

  def get_public_key(self, pwtxid):
    key = RSAKeyPairs(self.oracle.db).get_by_pwtxid(pwtxid)
    if key:
      return key['public']

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

  def handle_request(self, request):
    message = request.message

    if not self.try_prepare_raw_transaction(message):
      logging.debug('transaction looks invalid, ignoring')
      return

    pwtxid = self.oracle.btc.add_multisig_address(message['req_sigs'], message['pubkey_list'])

    if LockedPasswordTransaction(self.oracle.db).get_by_pwtxid(pwtxid):
      logging.info('pwtxid already in use. did you resend the same request?')
      return

    pub_key = self.get_public_key(pwtxid)
    message['rsa_pubkey'] = json.loads(pub_key)
    message['operation'] = 'new_bounty'
    message['pwtxid'] = pwtxid

    locktime = int(message['locktime'])

    LockedPasswordTransaction(self.oracle.db).save({'pwtxid':pwtxid, 'json_data':json.dumps(message)})

    logging.debug('broadcasting reply')

    self.oracle.communication.broadcast(message['operation'], json.dumps(message))
    self.oracle.task_queue.save({
        "operation": 'bounty_create',
        "json_data": json.dumps(request.message),
        "done": 0,
        "next_check": locktime
    })


  def handle_task(self, task):
    message = json.loads(task['json_data'])
    future_transaction = self.try_prepare_raw_transaction(message)
    assert(future_transaction is not None) # should've been verified gracefully in handle_request

    logging.debug('transaction ready to be signed')

    self.oracle.signer.sign(future_transaction, message['prevtxs'], message['req_sigs'])
