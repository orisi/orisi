from basehandler import BaseHandler

import json
import logging
from oracle.oracle_db import KeyValue
from random import randrange

class BountyQueryHandler(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    self.btc = oracle.btc
    self.kv = KeyValue(self.oracle.db)

  def handle_request(self, request):
    body = request.message

    bounty_name = body['bounty_name']
    bounty_hash = self.kv.get_by_section_key('bounty_name', bounty_name)
    if not bounty_hash:
      logging.info('transaction unknown')
      return

    password_hash = bounty_hash['password_hash']

    info_msg = {
      'operation': 'bounty_password_hash',
      'in_reply_to': body['message_id'],
      'password_hash': password_hash,
      'message_id': "%s-%s" % ("bounty_signature", str(randrange(1000000000,9000000000))),
      'contract_id' : "",
    }

    self.oracle.broadcast_with_fastcast(json.dumps(info_msg))
