# Main Oracle file
from oracle_communication import OracleCommunication
from db_connection import OracleDb, TaskQueue, UsedInput, SignedTransaction
from oracle_protocol import RESPONSE, SUBJECT
from condition_evaluator.evaluator import Evaluator

from settings_local import ORACLE_ADDRESS

from bitcoind_client.bitcoinclient import BitcoinClient
from bitmessage_communication.bitmessageclient import BitmessageClient

import time
import logging
import json
from xmlrpclib import ProtocolError

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
    # Future reference - add parsing condition. Now assumed true
    if not self.condition_valid(condition):
      logging.debug("condition invalid")
      return

    transaction = body['raw_transaction']
    prevtx = body['prevtx']
    pubkey_json = body['pubkey_json']
    try:
      pubkey_list = json.loads(pubkey_list)
    except ValueError:
      logging.debug("invalid json")
      return

    try:
      req_sigs = int(body['req_sigs'])
    except ValueError:
      logging.debug("req_sigs must be a number")
      return

    try:
      self.btc.addmultisigaddress(req_sigs, pubkey_list)
    except ProtocolError:
      logging.debug("cant add multisig address")
      return

    if not self.transaction_valid(transaction):
      logging.debug("transaction invalid")
      return

    if not self.btc.transaction_need_signature(transaction):
      logging.debug("transaction does not need a signature")
      return

    if not self.btc.transaction_contains_org_fee(transaction):
      logging.debug("org fee not found")
      return

    if not self.btc.transaction_contains_oracle_fee(transaction):
      logging.debug("oracle fee not found")
      self.communication.broadcast(SUBJECT.NO_FEE, RESPONSE.NO_FEE)
      return

    if self.btc.transaction_already_signed(transaction, prevtx):
      logging.debug("transaction already signed")
      return

    inputs, output = self.btc.get_inputs_outputs(transaction)

    used_input_db = UsedInput(self.db)
    for i in inputs:
      used_input = used_input_db.get_input(i)
      if used_input:
        if used_addres["json_out"] != output:
          self.broadcast(
              SUBJECT.ADDRESS_DUPLICATE,
              RESPONSE.ADDRESS_DUPLICATE)
          return
    for i in inputs:
      used_input_db.save({
          'input_hash': i,
          'json_out': output
      })

    locktime = int(body['locktime'])
    task_queue = TaskQueue(self.db).save({
        "json_data": message.message,
        "done": 0,
        "next_check": locktime
    })

  def handle_request(self, request):
    operation, message = request
    fun = self.operations[operation]
    fun(message)

    # Save object to database for future reference
    db_class = self.db.operations[operation]
    if db_class:
      db_class(self.db).save(message)

  def check_condition(self, condition):
    return self.evaluator.evaluate(condition)

  def handle_task(self, task):
    body = json.loads(task["json_data"])
    condition = body["condition"]
    transaction = body["raw_transaction"]
    if not self.check_condition(condition):
      self.task_queue.done(task)
      return
    if not self.transaction_valid(transaction):
      self.task_queue.done(task)
      return
    signed_transaction = self.btc.sign_transaction(transaction)
    body["raw_transaction"] = signed_transaction
    SignedTransaction().save({"hex_transaction": signed_transaction, "prevtx":body["prevtx"]})

    self.communication.broadcast_signed_transaction(json.dumps(body))
    self.task_queue.done(task)

  def run(self):
    
    if not ORACLE_ADDRESS:
      new_addr = self.btc.server.getnewaddress()
      logging.error("first run? add '%s' to ORACLE_ADDRESS in settings_local.py" % new_addr)
      exit()

    logging.info("my multisig address is %s" % ORACLE_ADDRESS)
    logging.debug("private key: %s" % self.btc.server.dumpprivkey(ORACLE_ADDRESS))

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