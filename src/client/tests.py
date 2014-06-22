from client import OracleClient, TransactionUnknownError
from client_db import ClientDb, MultisigRedeemDb, OracleListDb, RawTransactionDb
from test_data import ADDRESSES

from shared.bitcoind_client.bitcoinclient import BitcoinClient

from collections import Counter
from decimal import getcontext
from xmlrpclib import ProtocolError

import json
import os
import unittest

TEMP_CLIENT_DB_FILE = 'client_test.db'
TEST_ACCOUNT = 'client_test_account'
FAKE_TXID = '3bda4918180fd55775a24580652f4c26d898d5840c7e71313491a05ef0b743d8'

class MockBitmessageClient:
  pass

class MockClientDb(ClientDb):
  def __init__(self):
    self._filename = TEMP_CLIENT_DB_FILE
    self.connect()

class MockOracleClient(OracleClient):
  def __init__(self):
    getcontext().prec=8
    self.btc = BitcoinClient(account = TEST_ACCOUNT)
    self.bm = MockBitmessageClient()
    self.db = MockClientDb()

class ClientTests(unittest.TestCase):
  def setUp(self):
    self.client = MockOracleClient()

  def tearDown(self):
    os.remove(TEMP_CLIENT_DB_FILE)

    self.client = None

  def get_all_addresses(self):
    return sorted(self.client.btc.get_addresses_for_account(TEST_ACCOUNT))

  def get_client_pubkey_address(self):
    addresses = self.get_addresses(1)
    address = addresses[0]
    address_data = self.client.btc.validate_address(address)
    pubkey = address_data['pubkey']
    return pubkey, address

  def get_addresses(self, n):
    addresses = self.get_all_addresses()
    diff = max(n - len(addresses), 0)
    for i in range(diff):
      self.client.btc.get_new_address()
    addresses = self.get_all_addresses()[:n]
    return addresses

  def create_multisig(self):
    client_pubkey, _ = self.get_client_pubkey_address()
    oracles_pubkeys = [e['pubkey'] for e in ADDRESSES['oracles']]

    # 5 oracles, 3 signatures required
    req_sigs = 3

    result = self.client.create_multisig_address(client_pubkey, oracles_pubkeys, req_sigs)
    return result

  def create_fake_transaction(self, address):
    transaction = self.client.btc.create_multisig_transaction(
        [{"txid":FAKE_TXID, "vout":0}],
        {address:1.0}
    )
    return transaction

  def create_transaction(self):
    result = self.create_multisig()
    input_transaction = self.create_fake_transaction(result['address'])
    input_transaction_dict = self.client.btc._get_json_transaction(input_transaction)

    inputs = [{'txid': input_transaction_dict['txid'], 'vout':0}]
    _, client_address = self.get_client_pubkey_address()
    outputs = {client_address: 1.0}

    prevtxs = []
    script_pub_key = input_transaction_dict['vout'][0]['scriptPubKey']['hex']
    prevtx = {
        "scriptPubKey": script_pub_key,
        "redeemScript": result['redeemScript'],
        "txid": input_transaction_dict['txid'],
        "vout": 0
    }
    prevtxs.append(prevtx)

    return self.client.create_multisig_transaction(inputs, outputs), prevtxs

  def test_create_multisig_address_correct(self):
    result = self.create_multisig()

    # We should assume the created address will be 6 from 8
    # 3 of the pubkeys will be client_pubkeys
    address_result = self.client.btc.decode_script(result['redeemScript'])
    self.assertEquals(address_result['reqSigs'], 6)
    self.assertEquals(address_result['type'], 'multisig')
    addresses = address_result['addresses']
    self.assertEquals(len(addresses), 8)

    address_counter = Counter(addresses)
    client_pubkey, client_address = self.get_client_pubkey_address()
    self.assertEquals(address_counter[client_address], 3)

    expected_addresses = [e['address'] for e in ADDRESSES['oracles']]
    for addr in expected_addresses:
      self.assertEquals(address_counter[addr], 1)

    # Verify database
    db_object = MultisigRedeemDb(self.client.db).get_address(address_result['p2sh'])
    self.assertEquals(db_object['multisig'], address_result['p2sh'])
    self.assertEquals(db_object['min_sig'], 6)
    self.assertEquals(db_object['redeem_script'], result['redeemScript'])
    oracles_pubkeys = [e['pubkey'] for e in ADDRESSES['oracles']]
    self.assertEquals(db_object['pubkey_json'], json.dumps(sorted(oracles_pubkeys + 3 * [client_pubkey])))

  def test_create_multisig_address_invalid_pubkey(self):
    client_pubkey = "020323notavalidpubkey234"
    oracles_pubkeys = [e['pubkey'] for e in ADDRESSES['oracles']]
    req_sigs = 3

    with self.assertRaises(ProtocolError):
      self.client.create_multisig_address(client_pubkey, oracles_pubkeys, req_sigs)

  def test_add_oracle(self):
    for oracle in ADDRESSES['oracles']:
      self.client.add_oracle(oracle['pubkey'], oracle['address'], 0.0001)
    oracles = OracleListDb(self.client.db).get_all_oracles()
    self.assertEquals(len(oracles), len(ADDRESSES['oracles']))

  def test_update_oracle_list(self):
    self.client.update_oracle_list()
    oracles = OracleListDb(self.client.db).get_all_oracles()
    self.assertGreater(len(oracles), 0)

  def test_create_transaction(self):
    # If no errors occured then transaction is assumed to be valid
    self.create_transaction()

  def test_create_signed_transaction(self):
    unsigned_transaction, prevtx = self.create_transaction()
    signed_transaction = self.client.sign_transaction(unsigned_transaction, prevtx)
    self.assertEquals(self.client.btc.signatures_number(signed_transaction, prevtx), 3)

  def test_add_raw_transaction_valid(self):
    fake_transaction = self.create_fake_transaction(ADDRESSES['oracles'][0]['address'])
    self.client.add_raw_transaction(fake_transaction)
    transactions = RawTransactionDb(self.client.db).get_all_transactions()
    self.assertEquals(len(transactions), 1)

  def test_add_raw_transaction_invalid(self):
    fake_transaction = "00001023093842098"
    with self.assertRaises(ProtocolError):
      self.client.add_raw_transaction(fake_transaction)
    transactions = RawTransactionDb(self.client.db).get_all_transactions()
    self.assertEquals(len(transactions), 0)

  def test_get_amount_from_inputs_valid(self):
    fake_transaction = self.create_fake_transaction(ADDRESSES['oracles'][0]['address'])
    self.client.add_raw_transaction(fake_transaction)
    fake_transaction_dict = self.client.btc._get_json_transaction(fake_transaction)
    # We add the same transaction three times to see if client will count it only once
    inputs = [{'txid':fake_transaction_dict['txid'], 'vout':0}] * 3

    amount = self.client.get_amount_from_inputs(inputs)
    self.assertEquals(amount, 1.0)

  def test_get_amount_from_inputs_invalid(self):
    fake_transaction = self.create_fake_transaction(ADDRESSES['oracles'][0]['address'])
    fake_transaction_dict = self.client.btc._get_json_transaction(fake_transaction)
    inputs = [{'txid':fake_transaction_dict['txid'], 'vout':0}]
    with self.assertRaises(TransactionUnknownError):
      self.client.get_amount_from_inputs(inputs)
