from oracle import Oracle
from oracle_db import OracleDb, TaskQueue, TransactionRequestDb, HandledTransaction
from condition_evaluator.evaluator import Evaluator

from shared.bitmessage_communication.bitmessagemessage import BitmessageMessage
from shared.bitcoind_client.bitcoinclient import BitcoinClient

import base64
import json
import os
import unittest

from collections import defaultdict

TEMP_DB_FILE = 'temp_db_file.db'
TEST_ACCOUNT = 'oracle_test_account'
FAKE_TXID = '3bda4918180fd55775a24580652f4c26d898d5840c7e71313491a05ef0b743d8'
FAKE_PUBKEYS = [
  "0446ea8a207cb52c15c36bed7fb4cabc6d86df92ae0e1d32eb5274352c41fe763751150205aa93b07432030e9fe9f4a3e546925656c9ea69ab3977d5885215868d",
  "04ae31650f219e598a2c69beeb97867c9d3a292581af56ee156394f639ee4d6d7d19d2f4c9c565cc962fc5ecb5954edd1df13a8cd49962b8ebb78143c69cff7d6a",
  "04454a56bd5d554aff9001f330d87936aee45645b56139b3739dc50775c468813cfe74daca943a0d35252631f769618a4f33acb00f75a95f37d3cab55b07884309"
]
FAKE_PRIVKEYS = [
  "5JcfuBf6XcSARDjJsLuLB4JxBmVhHTHhGTqWUvsW5dPGEK6pW3i",
  "5KDdTzAiw5KZKALWk5jfxdTNwbPgVjqNf4fYdvq4pQT6enV7GrL",
  "5KQADM2LgH1JZDaSdYD6WwbukqCFFo54YDd62sE3KEnbXfscnxo"
]

def create_message(tx, prevtx, pubkeys):
  msg_dict = defaultdict(lambda: 'dummy')
  msg_dict['receivedTime'] = 1000
  msg_dict['subject'] = base64.encodestring('dummy')
  msg_dict['message'] = base64.encodestring("""
    {{
    "transactions": [{{
        "raw_transaction": "{0}",
        "prevtx": {1}
    }}],
    "pubkey_json": {2},
    "req_sigs": 4,
    "operation": "transaction",
    "locktime": 1402318623,
    "condition": "True"}}
    """.format(tx, prevtx, pubkeys))
  message = BitmessageMessage(
      msg_dict,
      'dummyaddress')
  return message


class MockOracleDb(OracleDb):
  def __init__(self):
    self._filename = TEMP_DB_FILE
    self.connect()
    operations = {
      'TransactionRequest': TransactionRequestDb
    }
    self.operations = defaultdict(lambda: False, operations)

class MockBitmessageCommunication:
  def broadcast_signed_transaction(self,msg_bd):
    pass

class MockOracle(Oracle):
  def __init__(self):
    self.communication = MockBitmessageCommunication()
    self.db = MockOracleDb()
    self.btc = BitcoinClient(account = TEST_ACCOUNT)
    self.evaluator = Evaluator()

    self.task_queue = TaskQueue(self.db)

    self.operations = {
      'TransactionRequest': self.add_transaction,
    }

class OracleTests(unittest.TestCase):
  def setUp(self):
    self.oracle = MockOracle()

  def tearDown(self):
    os.remove(TEMP_DB_FILE)

    # Bitcoind has limited rpc connections
    # We could change them in config, but we can just free resources
    self.oracle.btc = None
    self.oracle = None

  # Helping functions
  def get_all_addresses(self):
    return self.oracle.btc.get_addresses_for_account(TEST_ACCOUNT)

  def create_multisig(self):
    addresses = self.get_all_addresses()
    for i in range(max(0, 2 - len(addresses))):
      self.oracle.btc.get_new_address()
    addresses = self.get_all_addresses()[:2]
    pubkeys = [self.oracle.btc.validate_address(addr)['pubkey'] for addr in addresses]
    all_addresses = pubkeys + FAKE_PUBKEYS
    result = self.oracle.btc.create_multisig_address(4, all_addresses)
    multisig = result['address']
    redeem_script = result['redeemScript']
    self.oracle.btc.add_multisig_address(4, all_addresses)
    return multisig, redeem_script, all_addresses

  def create_unsigned_transaction(self):
    multisig, redeem_script, pubkeys = self.create_multisig()
    transaction = self.oracle.btc.create_multisig_transaction(
        [{"txid":FAKE_TXID, "vout":0}],
        {"1NJJpSgp55nQKe6DZkzg4VqxRRYcUuJSHz":1.0}
    )
    prevtxs = []
    prevtx = {
        "scriptPubKey": redeem_script,
        "redeemScript": redeem_script,
        "txid": FAKE_TXID,
        "vout": 0
    }
    prevtxs.append(prevtx)
    return (transaction, prevtxs, pubkeys)

  def create_signed_transaction(self):
    unsigned, prevtx, pubkeys = self.create_unsigned_transaction()
    signed = self.oracle.btc.sign_transaction(unsigned, prevtx, FAKE_PRIVKEYS)
    return signed, prevtx, pubkeys

  def create_request(self):
    transaction, prevtx, pubkeys = self.create_signed_transaction()
    message = create_message(transaction, json.dumps(prevtx), json.dumps(pubkeys))
    rqhs = self.oracle.get_request_hash(json.loads(message.message))
    request = ('TransactionRequest', message)
    return request, rqhs

  def add_request(self):
    request, rqhs = self.create_request()
    self.oracle.handle_request(request)
    return rqhs

  def test_add_transaction(self):
    self.add_request()
    self.assertEqual(len(self.oracle.task_queue.get_all_tasks()), 1)

  def test_add_task(self):
    self.add_request()
    task = self.oracle.task_queue.get_oldest_task()
    tasks = self.oracle.filter_tasks(task)
    self.assertEqual(len(tasks), 1)

    self.oracle.task_queue.done(tasks[0])

    task = self.oracle.task_queue.get_oldest_task()
    self.assertIsNone(task)

  def test_reject_task_more_sigs(self):
    request, rqhs = self.create_request()
    HandledTransaction(self.oracle.db).save({
        "rqhs": rqhs,
        "max_sigs": 4})

    self.oracle.handle_request(request)
    tasks = self.oracle.get_tasks()
    self.assertEqual(len(tasks), 0)

  def test_accept_task_same_sigs(self):
    request, rqhs = self.create_request()
    HandledTransaction(self.oracle.db).save({
        "rqhs": rqhs,
        "max_sigs":3})

    self.oracle.handle_request(request)
    tasks = self.oracle.get_tasks()
    self.assertEqual(len(tasks), 1)

  def test_update_task_less_sigs(self):
    request, rqhs = self.create_request()
    HandledTransaction(self.oracle.db).save({
        "rqhs": rqhs,
        "max_sigs":1})

    self.oracle.handle_request(request)
    tasks = self.oracle.get_tasks()
    self.assertEqual(len(tasks), 1)

    self.oracle.task_queue.done(tasks[0])

    self.assertEqual(HandledTransaction(self.oracle.db).signs_for_transaction(
        rqhs),
        3)

  def test_choosing_bigger_transaction(self):
    transaction, prevtx, pubkeys = self.create_unsigned_transaction()
    message = create_message(transaction, json.dumps(prevtx), json.dumps(pubkeys))
    request = ('TransactionRequest', message)
    self.oracle.handle_request(request)

    rqhs = self.add_request()

    self.assertEqual(len(self.oracle.task_queue.get_all_tasks()), 2)
    tasks = self.oracle.get_tasks()
    self.assertEqual(len(tasks), 1)
    task = tasks[0]
    body = json.loads(task['json_data'])
    transaction = body['transactions'][0]
    raw_transaction = transaction['raw_transaction']
    prevtx = transaction['prevtx']

    sigs = self.oracle.btc.signatures_number(raw_transaction, prevtx)
    self.assertEqual(sigs, 3)
    self.oracle.task_queue.done(task)

    self.assertEqual(HandledTransaction(self.oracle.db).signs_for_transaction(rqhs), 3)

  def test_no_tasks(self):
    tasks = self.oracle.get_tasks()
    self.assertIsInstance(tasks, list)
    self.assertEqual(len(tasks), 0)
