from basetaskhandler import BaseTaskHandler
from oracle.condition_evaluator.evaluator import Evaluator
from oracle.oracle_db import SignedTransaction, HandledTransaction

import json
import logging
import re

class ConditionedTransactionTaskHandler(BaseTaskHandler):
  def __init__(self, oracle):
    self.oracle = oracle
    self.evaluator = Evaluator()

  def handle_task(self, task):
    body = json.loads(task['json_data'])
    condition = body['condition']
    transactions = body['transactions']

    permissions_to_sign = self.evaluator.permissions_to_sign(condition, transactions)

    if sum(permissions_to_sign) == 0:
      logging.debug('no signatures for tx')
      self.oracle.task_queue.done(task)
      return

    for idx, tx in enumerate(transactions):
      if permissions_to_sign[idx]:
        transaction = tx['raw_transaction']
        prevtx = tx['prevtx']
        signed_transaction = self.oracle.btc.sign_transaction(transaction, prevtx)
        body['transactions'][idx]['raw_transaction'] = signed_transaction
        SignedTransaction(self.oracle.db).save({
            "hex_transaction": signed_transaction,
            "prevtx":json.dumps(prevtx)})

    self.oracle.communication.broadcast_signed_transaction(json.dumps(body))
    self.oracle.task_queue.done(task)

  def filter_tasks(self, task):
    rqhs = task['filter_field']
    match = re.match(r'^rqhs:(.*)', rqhs)
    if not match:
      return
    rqhs = match.group(1)

    other_tasks = self.oracle.task_queue.get_similar(task)
    most_signatures = 0
    task_sig = []
    for task in other_tasks:
      body = json.loads(task['json_data'])

      transactions = body['transactions']
      min_sig_for_tx = 999
      for tx in transactions:
        raw_transaction = tx['raw_transaction']
        prevtx = tx['prevtx']
        signatures_for_tx = self.oracle.btc.signatures_number(
            raw_transaction,
            prevtx)
        min_sig_for_tx = min(min_sig_for_tx, signatures_for_tx)
      task_sig.append((task, min_sig_for_tx))
      most_signatures = max(most_signatures, signatures_for_tx)

    # If there is already a transaction that has MORE signatures than what we
    # have here - then ignore all tasks
    signs_for_transaction = HandledTransaction(self.oracle.db).signs_for_transaction(rqhs)

    if signs_for_transaction > most_signatures:
      tasks_to_do = []
      redundant = [t[0] for t in task_sig]
    else:
      tasks_to_do = [t[0] for t in task_sig if t[1] == most_signatures]
      redundant = [t[0] for t in task_sig if t not in tasks_to_do]

    HandledTransaction(self.oracle.db).update_tx(rqhs, most_signatures)
    for r in redundant:
      self.oracle.task_queue.done(r)
    return tasks_to_do
