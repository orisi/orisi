# Main Oracle file
from oracle_communication import OracleCommunication
from db_connection import OracleDb, TaskQueue
from oracle_protocol import RESPONSE, SUBJECT

import time
import logging
import json

class Oracle:
  def __init__(self):
    self.communication = OracleCommunication()
    self.db = OracleDb()

    self.operations = {
      'PingRequest': self.ping,
      'TransactionRequest': self.transaction,
    }

  def condition_invalid(self, condition):
    return False

  def transaction_invalid(self, transaction):
    return False

  def transaction(self, message):
    body = json.loads(message.message)

    condition = body['condition']
    # Future reference - add parsing condition. Now assumed true
    if self.condition_invalid(condition):
      self.communication.response(
          message, 
          SUBJECT.INVALID_CONDITION, 
          RESPONSE.INVALID_CONDITION)
      return

    transaction = body['raw_transaction']
    if self.transaction_invalid(transaction):
      self.communication.response(
          message, 
          SUBJECT.INVALID_TRANSACTION, 
          RESPONSE.INVALID_TRANSACTION)
      return

    check_time = int(body['check_time'])
    task_queue = TaskQueue(self.db).save({
        "from_address": message.from_address,
        "json_data": message.message,
        "done": 0,
        "next_check": check_time
    })
    self.communication.response(message, SUBJECT.CONFIRMED, RESPONSE.CONFIRMED)

  def ping(self, message):
    if message.to_address == self.communication.default_address:
      self.communication.response(message, SUBJECT.PING, RESPONSE.PING)

  def handle_request(self, request):
    operation, message = request
    fun = self.operations[operation]
    fun(message)

    # Save object to database for future reference
    db_class = self.db.operations[operation]
    if db_class:
      db_class(self.db).save(message)

  def sign_transaction(self, transaction):
    # Placeholder for signing transactions
    return transaction

  def check_condition(self, condition):
    # Placeholder for checking condition
    return True

  def handle_task(self, task):
    body = json.loads(task["json_data"])
    condition = body["condition"]
    transaction = body["raw_transaction"]
    if not self.check_condition(condition):
      return
    signed_transaction = self.sign_transaction(transaction)

    self.communication.response_to_address(
        task["from_adderss"], 
        SUBJECT.TRANSACTION_SIGNED, 
        RESPONSE.TRANSACTION_SIGNED)
    self.communication.broadcast_signed_transaction(signed_transaction)

  def run(self):
    while True:
      # Proceed all requests
      logging.debug("Oracle Run")
      requests = self.communication.get_new_requests()
      for request in requests:
        self.handle_request(request)
        self.communication.mark_request_done(request)

      task = self.db.get_oldest_task()
      self.handle_task(task)

      time.sleep(1)