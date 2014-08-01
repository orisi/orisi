from basehandler import BaseHandler

import json

from oracle_db import KeyValue

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
    mark_history_entries.append({'mark':mark,'addr':addr,'ts':data['ts']})
    self.kv.update('mark_history', '{}#{}'.format(mark, addr), mark_history_entries)

    self.kv.update('mark_available', '{}#{}'.format(mark, addr), {'available':False})

  def handle_new_block(self, block):
    transaction_ids = block['tx']

    our_addresses = self.kv.get_by_section_key('safe_timelock', 'addresses')
    if not our_addresses:
      return

    our_addresses = our_addresses['addresses']

    outputs = []
    for tx in transaction_ids:
      raw_transaction = self.btc.get_raw_transaction(tx)
      transaction = self.btc.decode_raw_transaction(raw_transaction)
      for vout in transaction['vout']:
        if len(vout['scriptPubKey']['addresses']) != 1:
          continue
        if vout['scriptPubKey']['addresses'][0] in our_addresses:
          outputs.append((vout['value'], vout['scriptPubKey']['addresses'][0]))

