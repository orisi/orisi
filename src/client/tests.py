from client import OracleClient
from client_db import ClientDb, MultisigRedeemDb, OracleListDb
from test_data import ADDRESSES

from shared.bitcoind_client.bitcoinclient import BitcoinClient

from collections import Counter
from decimal import getcontext
from xmlrpclib import ProtocolError

import json
import os
import unittest

TEMP_CLIENT_DB_FILE = 'client_test.db'

class MockBitmessageClient:
  pass

class MockClientDb(ClientDb):
  def __init__(self):
    self._filename = TEMP_CLIENT_DB_FILE
    self.connect()

class MockOracleClient(OracleClient):
  def __init__(self):
    getcontext().prec=8
    self.btc = BitcoinClient()
    self.bm = MockBitmessageClient()
    self.db = MockClientDb()

class ClientTests(unittest.TestCase):
  def setUp(self):
    self.client = MockOracleClient()

  def tearDown(self):
    os.remove(TEMP_CLIENT_DB_FILE)

    self.client = None

  def test_create_multisig_address_correct(self):
    client_pubkey = ADDRESSES['client_pubkey']
    oracles_pubkeys = [e['pubkey'] for e in ADDRESSES['oracles']]

    # 5 oracles, 3 signatures required
    req_sigs = 3

    result = self.client.create_multisig_address(client_pubkey, oracles_pubkeys, req_sigs)

    # We should assume the created address will be 6 from 8
    # 3 of the pubkeys will be client_pubkeys
    address_result = self.client.btc.decode_script(result['redeemScript'])
    self.assertEquals(address_result['reqSigs'], 6)
    self.assertEquals(address_result['type'], 'multisig')
    addresses = address_result['addresses']
    self.assertEquals(len(addresses), 8)

    address_counter = Counter(addresses)
    self.assertEquals(address_counter[ADDRESSES['client_address']], 3)

    expected_addresses = [e['address'] for e in ADDRESSES['oracles']]
    for addr in expected_addresses:
      self.assertEquals(address_counter[addr], 1)

    # Verify database
    db_object = MultisigRedeemDb(self.client.db).get_address(address_result['p2sh'])
    self.assertEquals(db_object['multisig'], address_result['p2sh'])
    self.assertEquals(db_object['min_sig'], 6)
    self.assertEquals(db_object['redeem_script'], result['redeemScript'])
    self.assertEquals(db_object['pubkey_json'], json.dumps(sorted(oracles_pubkeys + 3 * [client_pubkey])))

  def test_create_multisig_address_invalid_pubkey(self):
    client_pubkey = "020323notavalidpubkey234"
    oracles_pubkeys = [e['pubkey'] for e in ADDRESSES['oracles']]
    req_sigs = 3

    with self.assertRaises(ProtocolError):
      self.client.create_multisig_address(client_pubkey, oracles_pubkeys, req_sigs)

  def test_add_oracle(self):
    self.client.add_oracle(ADDRESSES['client_pubkey'], ADDRESSES['client_address'], 0.0001)
    oracles = OracleListDb(self.client.db).get_all_oracles()
    self.assertEquals(len(oracles), 1)

  def test_update_oracle_list(self):
    self.client.update_oracle_list()
    oracles = OracleListDb(self.client.db).get_all_oracles()
    self.assertGreater(len(oracles), 0)
