# Main Oracle file
from oracle_communication import OracleCommunication
from oracle_db import OracleDb, TaskQueue
from handlers.handlers import handlers
from condition_evaluator.evaluator import Evaluator

from settings_local import ORACLE_ADDRESS, ORACLE_FEE
from shared.bitcoind_client.bitcoinclient import BitcoinClient

import time
import logging

from collections import defaultdict
from decimal import Decimal

# 3 minutes between oracles should be sufficient
HEURISTIC_ADD_TIME = 60 * 3

class Oracle:
  def __init__(self):
    self.communication = OracleCommunication()
    self.db = OracleDb()
    self.btc = BitcoinClient()
    self.evaluator = Evaluator()

    self.task_queue = TaskQueue(self.db)

    self.handlers = defaultdict(lambda: None, handlers)

  def get_inputs_outputs(self, transactions):
    all_inputs = set()
    all_outputs = []

    for transaction in transactions:
      inputs, output = self.btc.get_inputs_outputs(transaction)
      for i in inputs:
        all_inputs.add(i)
      all_outputs.append(sorted(output))

    all_inputs = sorted(list(all_inputs))
    return (all_inputs, all_outputs)

  def handle_request(self, request):
    operation, message = request
    handler = self.handlers[operation]

    if not handler:
      logging.debug("operation {} not supported".format(operation))
      return

    handler(self).handle_request(message)

    # Save object to database for future reference
    db_class = self.db.operations[operation]
    if db_class:
      db_class(self.db).save(message)

  def handle_task(self, task):
    operation = task['operation']
    handler = self.handlers[operation]
    if handler:
      handler(self).handle_task(task)
    else:
      logging.debug("Task has invalid operation")
      self.task_queue.done(task)

  def get_tasks(self):
    task = self.task_queue.get_oldest_task()
    if not task:
      return []

    operation = task['operation']
    handler = self.handlers[operation]
    if handler:
      tasks = handler(self).filter_tasks(task)
      return tasks
    else:
      logging.debug("Task has invalid operation")
      self.task_queue.done(task)

  def is_fee_sufficient(self, addr, fee):
    if addr != ORACLE_ADDRESS:
      return False
    if fee < Decimal(ORACLE_FEE):
      return False
    return True

  def run(self):

    if not ORACLE_ADDRESS:
      new_addr = self.btc.server.getnewaddress()
      logging.error("first run? add '%s' to ORACLE_ADDRESS in src/settings_local.py" % new_addr)
      exit()

    logging.info("my multisig address is %s" % ORACLE_ADDRESS)

    while True:
      # Proceed all requests
      requests = self.communication.get_new_requests()
      logging.debug("{0} new requests".format(len(requests)))
      for request in requests:
        self.handle_request(request)
        self.communication.mark_request_done(request)

      tasks = self.get_tasks()
      for task in tasks:
        self.handle_task(task)

      time.sleep(1)
