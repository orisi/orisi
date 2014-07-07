# Main Oracle file
from oracle_communication import OracleCommunication
from oracle_db import OracleDb, TaskQueue
from handlers.handlers import op_handlers

from settings_local import ORACLE_ADDRESS, ORACLE_FEE
from shared.bitcoind_client.bitcoinclient import BitcoinClient

from handlers.transactionsigner import TransactionSigner

import time
import logging

from decimal import Decimal

# 3 minutes between oracles should be sufficient
HEURISTIC_ADD_TIME = 60 * 3

class Oracle:
  def __init__(self):
    self.communication = OracleCommunication()
    self.db = OracleDb()
    self.btc = BitcoinClient()

    self.task_queue = TaskQueue(self.db)

    self.handlers = op_handlers
    self.signer = TransactionSigner(self)

  def handle_request(self, request):
    operation, message = request
    
    if not operation in self.handlers:
      logging.debug("operation {} not supported".format(operation))
      return

    handler = self.handlers[operation]

    try:
      handler(self).handle_request(message)
    except:
      logging.exception('error handling the request')


    # Save object to database for future reference
    db_class = self.db.operations[operation]
    if db_class:
      db_class(self.db).save(message)

  def handle_task(self, task):
    operation = task['operation']
    assert(operation in self.handlers)
    handler = self.handlers[operation]
    handler(self).handle_task(task)

    operation = task['operation']
    handler = self.handlers[operation]
    if handler:
      if handler(self).valid_task(task):
        return task
      else:
        logging.debug('Task marked as invalid by handler')
        self.task_queue.done(task)
        return None
    else:
      logging.debug("Task has invalid operation")
      self.task_queue.done(task)
      return None

  def is_fee_sufficient(self, addr, fee):
    if addr != ORACLE_ADDRESS:
      return False
    if fee < Decimal(ORACLE_FEE):
      return False
    return True

  def run(self):

    if not ORACLE_ADDRESS:
      new_addr = self.btc.server.getnewaddress()
      logging.error("first run? please add '%s' to ORACLE_ADDRESS in src/settings_local.py" % new_addr)
      exit()

    logging.info("my multisig address is %s" % ORACLE_ADDRESS)
    logging.info( "my pubkey: %r" % self.btc.validate_address(ORACLE_ADDRESS)['pubkey'] )

    logging.debug("awaiting requests...")
    count = 0

    while True:
      # Proceed all requests
      requests = self.communication.get_new_requests()
      if len(requests) == 0:
        count = count + 1
        if count > 30:
            logging.debug("{0} new requests".format(len(requests)))
            count = 0
      else:
        logging.debug("{0} new requests".format(len(requests)))

      for request in requests:
        self.handle_request(request)
        self.communication.mark_request_done(request)

      task = self.task_queue.get_oldest_task()
      while task is not None:
        self.handle_task(task)
        self.task_queue.done(task)
        task = self.task_queue.get_oldest_task()


      time.sleep(1)
