# Main Oracle file
from oracle_communication import OracleCommunication
from oracle_db import OracleDb, TaskQueue, UsedInput, SignedTransaction, HandledTransaction
from oracle_protocol import RESPONSE, SUBJECT
from condition_evaluator.evaluator import Evaluator

from settings_local import ORACLE_ADDRESS
from shared.bitcoind_client.bitcoinclient import BitcoinClient

import hashlib
import time
import logging
import json
import re
from xmlrpclib import ProtocolError

# 3 minutes between oracles should be sufficient
HEURISTIC_ADD_TIME = 60 * 3

class TransactionVerificationError(Exception):
  pass

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

  def inputs_addresses(self, prevtxs):
    addresses = set()
    for prevtx in prevtxs:
      if not 'redeemScript' in prevtx:
        return False
      script = prevtx['redeemScript']
      address = self.btc.get_address_from_script(script)
      addresses.add(address)
    return list(addresses)

  def inputs_from_same_address(self, prevtxs):
    addresses = self.inputs_addresses(prevtxs)
    if len(addresses) != 1:
      return False
    return True

  def verify_transaction(self, tx):
    transaction = tx['raw_transaction']
    prevtx = tx['prevtx']

    if not self.transaction_valid(transaction):
      logging.debug("transaction invalid")
      raise TransactionVerificationError()

    if not self.inputs_from_same_address(prevtx):
      logging.debug("all inputs should go from the same multisig address")
      raise TransactionVerificationError()

    if not self.includes_me(prevtx):
      logging.debug("transaction does not include me")
      raise TransactionVerificationError()

    if not self.btc.transaction_contains_org_fee(transaction):
      logging.debug("org fee not found")
      raise TransactionVerificationError()

    if not self.btc.transaction_contains_oracle_fee(transaction):
      logging.debug("oracle fee not found")
      raise TransactionVerificationError()

    if self.btc.transaction_already_signed(transaction, prevtx):
      logging.debug("transaction already signed")
      raise TransactionVerificationError()

  def get_request_hash(self, request):
    raw_transactions = [tx['raw_transaction'] for tx in request['transactions']]
    inputs, outputs = self.get_inputs_outputs(raw_transactions)
    request_dict= {
        "inputs": inputs,
        "outputs": outputs,
        "locktime": request['locktime'],
        "condition": request['condition']
    }
    return hashlib.sha256(json.dumps(request_dict)).hexdigest()

  def get_inputs_outputs(self, transactions):
    all_inputs = set()
    all_outputs = []

    for transaction in transactions:
      inputs, output = self.btc.get_inputs_outputs(transaction)
      for i in inputs:
          all_inputs.add(i)
      all_outputs.extend(output)

    all_inputs = sorted(list(all_inputs))
    all_outputs = sorted(all_outputs)
    return (all_inputs, all_outputs)

  def add_transaction(self, message):
    body = json.loads(message.message)

    pubkey_list = body['pubkey_json']
    try:
      req_sigs = int(body['req_sigs'])
    except ValueError:
      logging.debug("req_sigs must be a number")
      return

    try:
      locktime = int(body['locktime'])
    except ValueError:
      logging.debug("locktime must be a number")
      return

    condition = body['condition']
    # Future reference - add parsing condition. Now assumed true
    if not self.condition_valid(condition):
      logging.debug("condition invalid")
      return

    try:
      self.btc.add_multisig_address(req_sigs, pubkey_list)
    except ProtocolError:
      logging.debug("cant add multisig address")
      return

    transactions = body['transactions']
    for tx in transactions:
      try:
        self.verify_transaction(tx)
      except TransactionVerificationError:
        return

    raw_transactions = [tx['raw_transaction'] for tx in transactions]
    all_inputs, all_outputs = self.get_inputs_outputs(raw_transactions)


    rq_hash = self.get_request_hash(body)

    used_input_db = UsedInput(self.db)
    for i in all_inputs:
      used_input = used_input_db.get_input(i)
      if used_input:
        if used_input["json_out"] != rq_hash:
          self.broadcast(
              SUBJECT.ADDRESS_DUPLICATE,
              RESPONSE.ADDRESS_DUPLICATE)
          return
    for i in all_inputs:
      used_input_db.save({
          'input_hash': i,
          'json_out': rq_hash
      })

    all_turns = []
    for transaction in transactions:
      prevtx = transaction['prevtx']
      turns = [self.get_my_turn(tx['redeemScript']) for tx in prevtx if 'redeemScript' in tx]
      my_turn = max(turns)
      all_turns.append(my_turn)

    my_turn = max(all_turns)
    add_time = my_turn * HEURISTIC_ADD_TIME

    self.task_queue.save({
        "json_data": message.message,
        "filter_field": 'rqhs:{}'.format(rq_hash),
        "done": 0,
        "next_check": locktime + add_time
    })

  def handle_request(self, request):
    operation, message = request
    fun = self.operations[operation]
    fun(message)

    # Save object to database for future reference
    db_class = self.db.operations[operation]
    if db_class:
      db_class(self.db).save(message)

  def get_my_turn(self, redeem_script):
    """
    Returns which one my address is in sorted (lexicographically) list of all
    addresses included in redeem_script.
    """
    addresses = sorted(self.btc.addresses_for_redeem(redeem_script))
    for idx, addr in enumerate(addresses):
      if self.btc.address_is_mine(addr):
        return idx
    return -1

  def includes_me(self, prevtx):
    for tx in prevtx:
      if not 'redeemScript' in tx:
        return False
      my_turn = self.get_my_turn(tx['redeemScript'])
      if my_turn < 0:
        return False
    return True

  def handle_task(self, task):
    body = json.loads(task['json_data'])
    condition = body['condition']
    transactions = body['transactions']

    permissions_to_sign = self.evaluator.permissions_to_sign(condition, transactions)

    if sum(permissions_to_sign) == 0:
      logging.debug('no signatures for tx')
      self.task_queue.done(task)
      return False

    for idx, tx in enumerate(transactions):
      if permissions_to_sign[idx]:
        transaction = tx['raw_transaction']
        prevtx = tx['prevtx']
        signed_transaction = self.btc.sign_transaction(transaction, prevtx)
        body['transactions'][idx]['raw_transaction'] = signed_transaction
        SignedTransaction(self.db).save({
            "hex_transaction": signed_transaction,
            "prevtx":json.dumps(prevtx)})

    self.communication.broadcast_signed_transaction(json.dumps(body))
    self.task_queue.done(task)

  def filter_tasks(self, task):
    rqhs = task['filter_field']
    match = re.match(r'^rqhs:(.*)', rqhs)
    if not match:
      return
    rqhs = match.group(1)

    other_tasks = self.task_queue.get_similar(task)
    most_signatures = 0
    task_sig = []
    for task in other_tasks:
      body = json.loads(task['json_data'])

      transactions = body['transactions']
      min_sig_for_tx = 999
      for tx in transactions:
        raw_transaction = tx['raw_transaction']
        prevtx = tx['prevtx']
        signatures_for_tx = self.btc.signatures_number(
            raw_transaction,
            prevtx)
        min_sig_for_tx = min(min_sig_for_tx, signatures_for_tx)
      task_sig.append((task, min_sig_for_tx))
      most_signatures = max(most_signatures, signatures_for_tx)

    # If there is already a transaction that has MORE signatures than what we
    # have here - then ignore all tasks
    signs_for_transaction = HandledTransaction(self.db).signs_for_transaction(rqhs)

    if signs_for_transaction > most_signatures:
      tasks_to_do = []
      redundant = [t[0] for t in task_sig]
    else:
      tasks_to_do = [t[0] for t in task_sig if t[1] == most_signatures]
      redundant = [t[0] for t in task_sig if t not in tasks_to_do]

    HandledTransaction(self.db).update_tx(rqhs, most_signatures)
    for r in redundant:
      self.task_queue.done(r)
    return tasks_to_do

  def get_tasks(self):
    task = self.task_queue.get_oldest_task()
    if task:
      tasks = self.filter_tasks(task)
      return tasks
    return []

  def run(self):

    if not ORACLE_ADDRESS:
      new_addr = self.btc.server.getnewaddress()
      logging.error("first run? add '%s' to ORACLE_ADDRESS in settings_local.py" % new_addr)
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
