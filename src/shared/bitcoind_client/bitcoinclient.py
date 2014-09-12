from settings_local import *

import json
import jsonrpclib
import time
from xmlrpclib import ProtocolError
from decimal import Decimal
import socket

import logging

TEST_MODE = True

class UnknownServerError(Exception):
  pass

class BitcoinClient:

  def __init__(self, account=None):
    self.account = account
    self.connect()
    self.blockchain_connect()

  def _connect(self, connection_function):
    try_factor = 1

    while 1:
      try:
        connection_function()
        return
      except:
        try_factor *= 2

        if try_factor > 512:
          logging.critical('can\'t connect to bitcoind server')
          return

        logging.info('can\'t connect to bitcoind server, waiting {}'.format(try_factor))
        time.sleep(try_factor)

  def connect(self):
    def server_connection():
      self.server = jsonrpclib.Server('http://{0}:{1}@{2}:{3}'.format(
          BITCOIND_RPC_USERNAME,
          BITCOIND_RPC_PASSWORD,
          BITCOIND_RPC_HOST,
          BITCOIND_RPC_PORT))
      socket.setdefaulttimeout(None)
      self.server.help()
    self._connect(server_connection)

  def blockchain_connect(self):
    """
    If your Oracle is in test mode, then blockchain server is different than default server
    """
    def server_connection():
      if TEST_MODE:
        self.blockchain_server = jsonrpclib.Server('http://{0}:{1}@{2}:{3}'.format(
            BITCOIND_TEST_RPC_USERNAME,
            BITCOIND_TEST_RPC_PASSWORD,
            BITCOIND_TEST_RPC_HOST,
            BITCOIND_TEST_RPC_PORT))
      else:
        self.blockchain_server = jsonrpclib.Server('http://{0}:{1}@{2}:{3}'.format(
            BITCOIND_RPC_USERNAME,
            BITCOIND_RPC_PASSWORD,
            BITCOIND_RPC_HOST,
            BITCOIND_RPC_PORT))
      socket.setdefaulttimeout(None)
      self.server.help()
    self._connect(server_connection)


  def keep_alive(server):
    def wrapper(fun):
      def ping_and_reconnect(self, *args, **kwargs):
        if server == 'server':
          server_instance = self.server
          connection_function = self.connect
        elif server == 'blockchain_server':
          server_instance = self.blockchain_server
          connection_function = self.blockchain_connect
        else:
          raise UnknownServerError()

        try:
          # Cheap API call that checks wether we're connected
          server_instance.help()
          response = fun(self, *args, **kwargs)
          return response
        except:
          connection_function()
        return fun(self, *args, **kwargs)
      return ping_and_reconnect
    return wrapper

  @keep_alive('server')
  def decode_raw_transaction(self, hex_transaction):
    return self.server.decoderawtransaction(hex_transaction)

  @keep_alive('server')
  def get_json_transaction(self, hex_transaction):
    return self.server.decoderawtransaction(hex_transaction)

  @keep_alive('server')
  def sign_transaction(self, raw_transaction, prevtx = [], priv_keys=None):
    if priv_keys:
      result = self.server.signrawtransaction(raw_transaction, prevtx, priv_keys)
    else:
      result = self.server.signrawtransaction(raw_transaction, prevtx)
    return result['hex']

  @keep_alive('server')
  def get_txid(self, raw_transaction):
    transaction_dict = self.server.decoderawtransaction(raw_transaction)
    return transaction_dict['txid']

  @keep_alive('server')
  def signatures_count(self, raw_transaction, prevtx):
    transaction_dict = self.server.decoderawtransaction(raw_transaction)

    prevtx_dict = {}
    for tx in prevtx:
      prevtx_dict["{}#{}".format(tx['txid'], tx['vout'])] = tx['redeemScript']

    has_signatures = 999
    for vin in transaction_dict['vin']:
      redeem_script = prevtx_dict["{}#{}".format(tx['txid'], tx['vout'])]
      try:
        asm = vin['scriptSig']['asm']
      except KeyError:
        logging.error('transaction doesn\'t have scriptSig asm')
        continue
      asm_elements = asm.split()
      try:
        asm_script_dict = self.server.decodescript(redeem_script)
        int(asm_script_dict['reqSigs'])
      except KeyError:
        logging.error('script is missing reqSigs field')
        continue
      # first elements is op_zero, last is script, rest is signatuers
      asm_signatures = asm_elements[1:-1]

      # if tried to sign a tx with the same signature again, the sig will equal '0', and we should ignore it
      current_signatures = 0
      for a in asm_signatures:
        if a != '0':
          current_signatures += 1
      has_signatures = min(has_signatures, current_signatures)
    return has_signatures


  @keep_alive('server')
  def signatures(self, raw_transaction, prevtx):
    transaction_dict = self.server.decoderawtransaction(raw_transaction)

    prevtx_dict = {}
    for tx in prevtx:
      prevtx_dict[str((tx['txid'], tx['vout']))] = tx['redeemScript']

    has_signatures = 999
    for vin in transaction_dict['vin']:
      redeem_script = prevtx_dict[str((vin['txid'], vin['vout']))]
      try:
        asm = vin['scriptSig']['asm']
      except KeyError:
        logging.error('transaction doesn\'t have scriptSig asm')
        continue
      asm_elements = asm.split()
      try:
        asm_script_dict = self.server.decodescript(redeem_script)
        int(asm_script_dict['reqSigs'])
      except KeyError:
        logging.error('script is missing reqSigs field')
        continue
      # first elements is op_zero, last is script, rest is signatuers
      return asm_elements
      current_signatures = len(asm_elements) - 2
      current_signatures = max(current_signatures, 0)
      has_signatures = min(has_signatures, current_signatures)
    return has_signatures

  @keep_alive('server')
  def is_valid_transaction(self, raw_transaction):
    # Is raw transaction valid and decodable?
    try:
      self.server.decoderawtransaction(raw_transaction)
    except ProtocolError:
      logging.exception('tx invalid')
      return False
    return True

  @keep_alive('server')
  def address_is_mine(self, address):
    result = self.server.validateaddress(address)
    return result['ismine']

  @keep_alive('server')
  def decode_script(self, script):
    return self.server.decodescript(script)

  @keep_alive('server')
  def get_inputs_outputs(self, raw_transaction):
    transaction_dict = self.server.decoderawtransaction(raw_transaction)
    vin = transaction_dict["vin"]
    vouts = transaction_dict["vout"]
    result = (
        sorted([json.dumps({'txid': tx_input['txid'], 'vout':tx_input['vout']}) for tx_input in vin]),
        json.dumps(
            {
              'vout': sorted([
                {
                  "value": vout["value"],
                  "scriptPubKey": vout["scriptPubKey"]["hex"]
                } for vout in vouts
              ])
            }
        )
    )

    return result

  @keep_alive('server')
  def transaction_already_signed(self, raw_transaction, prevtx):
    signed_transaction = self.sign_transaction(raw_transaction, prevtx)
    if signed_transaction == raw_transaction:
      return True
    return False

  @keep_alive('server')
  def transaction_need_signature(self, raw_transaction):
    """
    This is shameful ugly function. It tries to send transaction to network
    (even though we're working locally) and if it fails we know it still needs
    some signatures.
    """
    try:
      self.server.sendrawtransaction(raw_transaction)
      return False
    except ProtocolError:
      return True

  @keep_alive('server')
  def transaction_contains_output(self, raw_transaction, address, fee):
    transaction_dict = self.server.decoderawtransaction(raw_transaction)
    if not 'vout' in transaction_dict:
      return False
    for vout in transaction_dict['vout']:
      # Sanity checks
      if not 'value' in vout:
        continue
      if not 'scriptPubKey' in vout:
        continue
      if not 'addresses' in vout['scriptPubKey']:
        continue

      for address in vout['scriptPubKey']['addresses']:
        if address == address:
          value = Decimal(vout['value'])
          if value >= Decimal(fee):
            return True
    return False

  @keep_alive('server')
  def transaction_contains_oracle_fee(self, raw_transaction):
    return self.transaction_contains_output(raw_transaction, ORACLE_ADDRESS, ORACLE_FEE)

  @keep_alive('server')
  def transaction_contains_org_fee(self, raw_transaction):
    return self.transaction_contains_output(raw_transaction, ORGANIZATION_ADDRESS, ORGANIZATION_FEE)

  @keep_alive('server')
  def create_multisig_address(self, min_sigs, keys):
    keys = sorted(keys)
    return self.server.createmultisig(min_sigs, keys)

  @keep_alive('server')
  def add_multisig_address(self, min_sigs, keys):
    keys = sorted(keys)
    if self.account:
      return self.server.addmultisigaddress(min_sigs, keys, self.account)
    return self.server.addmultisigaddress(min_sigs, keys)

  @keep_alive('server')
  def create_raw_transaction(self, tx_inputs, outputs):
    return self.server.createrawtransaction(tx_inputs, outputs)

  @keep_alive('server')
  def get_new_address(self):
    if self.account:
      return self.server.getnewaddress(self.account)
    return self.server.getnewaddress()

  @keep_alive('server')
  def get_addresses_for_account(self, account):
    all_addresses = self.server.listreceivedbyaddress(0,True)
    addresses = [elt['address'] for elt in all_addresses if elt['account'] == account]
    return addresses

  @keep_alive('server')
  def validate_address(self, address):
    return self.server.validateaddress(address)

  @keep_alive('blockchain_server')
  def get_block_hash(self, block_number):
    try:
      return self.blockchain_server.getblockhash(block_number)
    except ProtocolError:
      return None

  @keep_alive('blockchain_server')
  def get_block(self, block_hash):
    return self.blockchain_server.getblock(block_hash)

  @keep_alive('blockchain_server')
  def get_block_count(self):
    return self.blockchain_server.getblockcount()

  @keep_alive('blockchain_server')
  def send_transaction(self, tx):
    try:
      self.blockchain_server.sendrawtransaction(tx)
      return True
    except ProtocolError:
      return False

  @keep_alive('blockchain_server')
  def get_raw_transaction(self, txid):
    return self.blockchain_server.getrawtransaction(txid)
