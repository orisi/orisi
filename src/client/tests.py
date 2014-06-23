from client import OracleClient, TransactionUnknownError, AddressMissingError, TooSmallAmountError
from client_db import ClientDb, MultisigRedeemDb, OracleListDb, RawTransactionDb, SignatureRequestDb
from test_data import ADDRESSES

from oracle.oracle_communication import OracleCommunication
from shared.bitcoind_client.bitcoinclient import BitcoinClient

from collections import Counter
from decimal import getcontext, Decimal
from xmlrpclib import ProtocolError

import json
import os
import unittest

TEMP_CLIENT_DB_FILE = 'client_test.db'
TEST_ACCOUNT = 'client_test_account'
FAKE_TXID = '3bda4918180fd55775a24580652f4c26d898d5840c7e71313491a05ef0b743d8'

class MockBitmessageClient:
  pass

class MockOracleCommunication(OracleCommunication):
  def __init__(self):
    self.client = MockBitmessageClient()

class MockClientDb(ClientDb):
  def __init__(self):
    self._filename = TEMP_CLIENT_DB_FILE
    self.connect()

class MockOracleClient(OracleClient):
  def __init__(self):
    getcontext().prec = 8
    self.btc = BitcoinClient(account = TEST_ACCOUNT)
    self.bm = MockBitmessageClient()
    self.db = MockClientDb()

class MockMessage():
  def __init__(self, msg):
    self.message = msg

class ClientTests(unittest.TestCase):
  def setUp(self):
    self.client = MockOracleClient()
    getcontext().prec = 8

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

  def create_multisig(self, blocking=True):
    client_pubkey, _ = self.get_client_pubkey_address()
    oracles_pubkeys = [e['pubkey'] for e in ADDRESSES['oracles']]

    # 5 oracles, 3 signatures required
    req_sigs = 3

    result = self.client.create_multisig_address(client_pubkey, oracles_pubkeys, req_sigs, blocking)
    return result

  def create_fake_transaction(self, address=ADDRESSES['oracles'][0]['address'], amount=1.0):
    transaction = self.client.btc.create_multisig_transaction(
        [{"txid":FAKE_TXID, "vout":0}],
        {address:amount}
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

  def test_create_multisig_address_blocking(self):
    address_result = self.create_multisig(blocking=False)
    script = address_result['redeemScript']
    script_dict = self.client.btc.decode_script(script)
    self.assertEquals(script_dict['reqSigs'], 4)
    addresses = script_dict['addresses']
    address_counter = Counter(addresses)
    client_pubkey, client_address = self.get_client_pubkey_address()
    expected_addresses = [e['address'] for e in ADDRESSES['oracles']]
    expected_addresses.append(client_address)

    self.assertEquals(len(expected_addresses), 6)
    for addr in expected_addresses:
      self.assertEquals(address_counter[addr], 1)

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
    fake_transaction = self.create_fake_transaction()
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
    fake_transaction = self.create_fake_transaction()
    self.client.add_raw_transaction(fake_transaction)
    fake_transaction_dict = self.client.btc._get_json_transaction(fake_transaction)
    # We add the same transaction three times to see if client will count it only once
    inputs = [{'txid':fake_transaction_dict['txid'], 'vout':0}] * 3

    amount = self.client.get_amount_from_inputs(inputs)
    self.assertEquals(amount, 1.0)

  def test_get_amount_from_inputs_invalid(self):
    fake_transaction = self.create_fake_transaction()
    fake_transaction_dict = self.client.btc._get_json_transaction(fake_transaction)
    inputs = [{'txid':fake_transaction_dict['txid'], 'vout':0}]
    with self.assertRaises(TransactionUnknownError):
      self.client.get_amount_from_inputs(inputs)

  def test_get_address(self):
    result = self.create_multisig()
    address = result['address']
    redeem = result['redeemScript']
    fake_transaction = self.create_fake_transaction(address)
    fake_transaction_dict = self.client.btc._get_json_transaction(fake_transaction)
    self.client.add_raw_transaction(fake_transaction)

    tx_input = {'txid': fake_transaction_dict['txid'], 'vout': 0}
    self.assertEquals(redeem, self.client.get_address(tx_input)['redeem_script'])

  def test_get_address_invalid_missing_address(self):
    fake_transaction = self.create_fake_transaction()
    fake_transaction_dict = self.client.btc._get_json_transaction(fake_transaction)
    self.client.add_raw_transaction(fake_transaction)

    tx_input = {'txid': fake_transaction_dict['txid'], 'vout': 0}
    with self.assertRaises(AddressMissingError):
      self.client.get_address(tx_input)

  def test_get_address_invalid_unknown_transaction(self):
    fake_transaction = self.create_fake_transaction()
    fake_transaction_dict = self.client.btc._get_json_transaction(fake_transaction)

    tx_input = {'txid': fake_transaction_dict['txid'], 'vout': 0}
    with self.assertRaises(TransactionUnknownError):
      self.client.get_address(tx_input)

  def test_prepare_prevtx_valid(self):
    result = self.create_multisig()
    address = result['address']
    redeem = result['redeemScript']
    fake_transaction = self.create_fake_transaction(address)
    fake_transaction_dict = self.client.btc._get_json_transaction(fake_transaction)
    script = fake_transaction_dict['vout'][0]['scriptPubKey']['hex']
    self.client.add_raw_transaction(fake_transaction)

    prevtx = [{'txid': fake_transaction_dict['txid'], 'vout': 0}]
    prevtx = self.client.prepare_prevtx(prevtx)
    prevtx = prevtx[0]
    self.assertEquals(redeem, prevtx['redeemScript'])
    self.assertEquals(script, prevtx['scriptPubKey'])

  def test_prepare_prevtx_invalid_unknown_transaction(self):
    fake_transaction = self.create_fake_transaction()
    fake_transaction_dict = self.client.btc._get_json_transaction(fake_transaction)

    prevtx = [{'txid': fake_transaction_dict['txid'], 'vout': 0}]
    with self.assertRaises(TransactionUnknownError):
      prevtx = self.client.prepare_prevtx(prevtx)

  def test_prepare_prevtx_invalid_missing_address(self):
    fake_transaction = self.create_fake_transaction()
    fake_transaction_dict = self.client.btc._get_json_transaction(fake_transaction)
    self.client.add_raw_transaction(fake_transaction)

    prevtx = [{'txid': fake_transaction_dict['txid'], 'vout': 0}]
    with self.assertRaises(AddressMissingError):
      prevtx = self.client.prepare_prevtx(prevtx)

  def create_fake_request(self, amount = 1.0):
    result = self.create_multisig()
    address = result['address']
    fake_transaction = self.create_fake_transaction(address, amount)
    fake_transaction_dict = self.client.btc._get_json_transaction(fake_transaction)
    self.client.add_raw_transaction(fake_transaction)

    inputs = [{'txid':fake_transaction_dict['txid'], 'vout':0}]

    for oracle in ADDRESSES['oracles']:
      self.client.add_oracle(oracle['pubkey'], oracle['address'], 0.0001)

    oracle_addresses = [e['address'] for e in ADDRESSES['oracles']]
    receiver_address = self.get_addresses(2)[-1]
    return self.client.create_request(
        inputs,
        receiver_address,
        oracle_addresses,
        100)

  def test_create_request_valid(self):
    request = self.create_fake_request()
    receiver_address = self.get_addresses(2)[-1]

    self.assertEquals(
        'conditioned_transaction',
        MockOracleCommunication().corresponds_to_protocol(MockMessage(request)))

    request_dict = json.loads(request)
    self.assertEquals(request_dict['req_sigs'], 6)
    self.assertEquals(request_dict['locktime'], 100)
    self.assertEquals(request_dict['operation'], 'conditioned_transaction')

    transactions = request_dict['transactions']
    self.assertEquals(len(transactions), 1)

    transaction = transactions[0]
    self.assertEquals(self.client.btc.signatures_number(transaction['raw_transaction'], transaction['prevtx']), 3)
    transaction_dict = self.client.btc._get_json_transaction(transaction['raw_transaction'])

    outs = transaction_dict['vout']
    output_sum = sum([Decimal(o['value']) for o in outs])
    # Fee for miners included?
    self.assertEquals(output_sum, Decimal("0.9999"))

    outputs = {}
    for o in outs:
      outputs[o['scriptPubKey']['addresses'][0]] = Decimal(o['value'])
    for oracle in ADDRESSES['oracles']:
      self.assertAlmostEqual(outputs[oracle['address']], Decimal("0.0001"), 8)
    self.assertAlmostEqual(outputs[receiver_address], Decimal("0.9994"), 8)

  def test_create_request_invalid_not_enough_for_oracles(self):
    with self.assertRaises(TooSmallAmountError):
      self.create_fake_request(0.0004)

  def test_create_request_invalid_not_enough_for_receiver(self):
    with self.assertRaises(TooSmallAmountError):
      self.create_fake_request(0.0006)

  def test_save_transaction_valid(self):
    request = self.create_fake_request()
    self.client.save_transaction(request)

    requests = SignatureRequestDb(self.client.db).get_all()
    self.assertEquals(len(requests), 1)
    self.assertEquals(request, requests[0]['json_data'])
