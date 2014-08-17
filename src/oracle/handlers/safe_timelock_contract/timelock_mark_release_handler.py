from basehandler import BaseHandler

import json
import cjson
import datetime
import time

from oracle.oracle_db import KeyValue
from contract_util import value_to_mark
from xmlrpclib import ProtocolError

class TimelockMarkReleaseHandler(BaseHandler):
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

    self.oracle.task_queue.save({
        "operation": 'safe_timelock_create',
        "json_data": cjson.encode({
            'mark': mark,
            'return_address': return_address,
            'oracle_fees': oracle_fees,
            'req_sigs': req_sigs,
            'miners_fee_satoshi': miners_fee_satoshi,
            'address': address,
            'value': value,
            'txid': txid,
            'n': n}),
        "done": 0,
        "next_check": locktime
    })

  def handle_new_block(self, block):
    transaction_ids = block['tx']

    our_addresses = self.kv.get_by_section_key('safe_timelock', 'addresses')
    if not our_addresses:
      return

    our_addresses = our_addresses['addresses']

    outputs = []
    for tx in transaction_ids:
      try:
        raw_transaction = self.btc.get_raw_transaction(tx)
      except ProtocolError:
        continue
      transaction = self.btc.decode_raw_transaction(raw_transaction)
      for vout in transaction['vout']:
        if not 'addresses' in vout['scriptPubKey']:
          continue
        if len(vout['scriptPubKey']['addresses']) != 1:
          continue
        if vout['scriptPubKey']['addresses'][0] in our_addresses:
          outputs.append((value_to_mark(vout['value']), vout['scriptPubKey']['addresses'][0], vout['value'], tx, vout['n']))

    for output in outputs:
      self.verify_and_create_timelock(output)


