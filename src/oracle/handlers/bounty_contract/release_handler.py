from basehandler import BaseHandler

import json
import cjson
import datetime
import logging
import time

from oracle.oracle_db import KeyValue
from contract_util import value_to_mark
from random import randrange

class BountyReleaseHandler(BaseHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    self.btc = oracle.btc
    self.kv = KeyValue(self.oracle.db)

  def handle_task(self, task):
    data = json.loads(task['json_data'])

    mark = data['mark']
    addr = data['address']

    mark_data = self.kv.get_by_section_key('mark_available', '{}#{}'.format(mark, addr))

    if not mark_data:
      return

    mark_history = self.kv.get_by_section_key('mark_history', '{}#{}'.format(mark, addr))

    if not mark_history:
      self.kv.store('mark_history', '{}#{}'.format(mark, addr), {'entries':[]})

    mark_history_entries = self.kv.get_by_section_key('mark_history', '{}#{}'.format(mark, addr))['entries']
    mark_history_entries.append({'mark':mark,'addr':addr,'ts': int(time.mktime(datetime.datetime.utcnow().timetuple()))})
    mark_history_dict = {"entries":mark_history_entries}
    self.kv.update('mark_history', '{}#{}'.format(mark, addr), mark_history_dict)

    self.kv.update('mark_available', '{}#{}'.format(mark, addr), {'available':True})
    logging.info("released mark {} from addr {}".format(mark, addr))

    info_msg = {
      'operation': 'bounty_released_mark',
      'in_reply_to': 'none',
      'message_id': "%s-%s" % ("mark-release", str(randrange(1000000000,9000000000))),
      'contract_id' : "{}#{}".format(addr, mark),
    }

    self.oracle.broadcast_with_fastcast(json.dumps(info_msg))

  def verify_and_create_timelock(self, output):
    mark, address, value, txid, n = output

    mark_data = self.kv.get_by_section_key('mark_available', '{}#{}'.format(mark, address))
    if not mark_data:
      return

    if mark_data['available']:
      return

    return_address = mark_data['return_address']
    locktime = mark_data['locktime']
    oracle_fees = mark_data['oracle_fees']
    miners_fee_satoshi = mark_data['miners_fee_satoshi']
    req_sigs = mark_data['req_sigs']
    password_hash = mark_data['password_hash']

    json_data = cjson.encode({
            'mark': mark,
            'return_address': return_address,
            'password_hash': password_hash,
            'oracle_fees': oracle_fees,
            'req_sigs': req_sigs,
            'miners_fee_satoshi': miners_fee_satoshi,
            'address': address,
            'value': value,
            'txid': txid,
            'n': n})

    self.oracle.task_queue.save({
        "operation": 'bounty_create',
        "json_data": json_data,
        "done": 0,
        "next_check": locktime
    })

    logging.info("found transaction for mark:{} on address:{}".format(mark, address))
    info_msg = {
      'operation': 'bounty_found_transaction',
      'password_hash': 'password_hash',
      'in_reply_to': 'none',
      'message_id': "%s-%s" % ("locked_transaction", str(randrange(1000000000,9000000000))),
      'contract_id' : "{}#{}".format(address, mark),
    }

    self.oracle.broadcast_with_fastcast(json.dumps(info_msg))

  def get_observed_addresses(self):
    observed_addresses = self.kv.get_by_section_key('bounty', 'addresses')
    if not observed_addresses:
      self.kv.store('bounty', 'addresses', {'addresses':[]})

    observed_addresses = self.kv.get_by_section_key('bounty', 'addresses')
    observed_addresses = observed_addresses['addresses']
    return observed_addresses

  def handle_new_transactions(self, transactions):
    logging.info(transactions)

    our_addresses = self.kv.get_by_section_key('bounty', 'addresses')
    if not our_addresses:
      return

    our_addresses = our_addresses['addresses']

    outputs = []
    for transaction in transactions:
      for vout in transaction['vout']:
        if not 'addresses' in vout['scriptPubKey']:
          continue
        if len(vout['scriptPubKey']['addresses']) != 1:
          continue
        if vout['scriptPubKey']['addresses'][0] in our_addresses:
          outputs.append((value_to_mark(vout['value']), vout['scriptPubKey']['addresses'][0], vout['value'], transaction['txid'], vout['n']))
    for output in outputs:
      self.verify_and_create_timelock(output)

