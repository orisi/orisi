# Main Oracle file
from oracle_communication import OracleCommunication
from db_connection import OracleDb, TaskQueue, UsedAddress
from oracle_protocol import RESPONSE, SUBJECT
from condition_evaluator.evaluator import Evaluator

from bitcoind_client.bitcoinclient import BitcoinClient

import time
import logging
import json

class Oracle:
  def __init__(self):
    self.communication = OracleCommunication()
    self.db = OracleDb()
    self.btc = BitcoinClient()
    self.evaluator = Evaluator()

    self.task_queue = TaskQueue(self.db)

    self.operations = {
      'TransactionRequest': self.add_transaction,
    }

  def condition_valid(self, condition):
    return self.evaluator.valid(condition) 

  def transaction_valid(self, transaction):
    return self.btc.is_valid_transaction(transaction)

  def add_transaction(self, message):
    body = json.loads(message.message)

    condition = body['condition']
    origin_address = body['origin_address']
    # Future reference - add parsing condition. Now assumed true
    if not self.condition_valid(condition):
      self.communication.response_to_address(
          origin_address, 
          SUBJECT.INVALID_CONDITION, 
          RESPONSE.INVALID_CONDITION)
      return

    transaction = body['raw_transaction']
    if self.transaction_valid(transaction):
      self.communication.response_to_address(
          origin_address, 
          SUBJECT.INVALID_TRANSACTION, 
          RESPONSE.INVALID_TRANSACTION)
      return

    if self.btc.transaction_already_signed(transaction):
      return

    inputs_outputs = self.btc.get_inputs_outputs(transaction)
    multisig_address = self.btc.get_multisig_sender_address(transaction)

    used_address_db = UsedAddress(self.db)
    used_address = used_address_db.get_address(multisig_address)
    if used_address:
      #DANGER! SHOULD BE TESTED AND PREPARED OMG!
      #checking equality should be done key by key, json object does not preserve order, json list does
      if used_address["json_in_out"] != inputs_outputs:
        self.communication.response_to_address(
            origin_address,
            SUBJECT.ADDRESS_DUPLICATE,
            RESPONSE.ADDRESS_DUPLICATE)
        return
    else:
      used_address_db.save({
          "multisig_address": multisig_address,
          "json_in_out": inputs_outputs,
      })

    check_time = int(body['check_time'])
    task_queue = TaskQueue(self.db).save({
        "origin_address": body['origin_address'],
        "json_data": message.message,
        "done": 0,
        "next_check": check_time
    })
    self.communication.response_to_address(
        origin_address, 
        SUBJECT.CONFIRMED, 
        RESPONSE.CONFIRMED)

  def handle_request(self, request):
    operation, message = request
    fun = self.operations[operation]
    fun(message)

    # Save object to database for future reference
    db_class = self.db.operations[operation]
    if db_class:
      db_class(self.db).save(message)

  def sign_transaction(self, transaction):
    signed_transaction = self.btc.sign_transaction()
    return signed_transaction

  def check_condition(self, condition):
    return self.evaluator.evaluate(condition)

  def handle_task(self, task):
    body = json.loads(task["json_data"])
    condition = body["condition"]
    transaction = body["raw_transaction"]
    if not self.check_condition(condition):
      self.task_queue.done(task)
      return
    signed_transaction = self.sign_transaction(transaction)
    body["raw_transaction"] = signed_transaction

    self.communication.broadcast_signed_transaction(json.dumps(body))
    self.task_queue.done(task)

  def run(self):
    while True:
      # Proceed all requests
      requests = self.communication.get_new_requests()
      logging.debug("{0} new requests".format(len(requests)))
      for request in requests:
        self.handle_request(request)
        self.communication.mark_request_done(request)

      task = self.task_queue.get_oldest_task()
      if task:
        self.handle_task(task)

      time.sleep(1)