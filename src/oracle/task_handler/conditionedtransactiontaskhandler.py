from basetaskhandler import BaseTaskHandler
from oracle.condition_evaluator.evaluator import Evaluator
from oracle.oracle_db import SignedTransaction

import json
import logging

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
