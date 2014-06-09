import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from settings_local import *

import json
import jsonrpclib
from xmlrpclib import ProtocolError
from decimal import Decimal


class BitcoinClient:

  def __init__(self):
    self.connect()

  def connect(self):
    self.server = jsonrpclib.Server('http://{0}:{1}@{2}:{3}'.format(
        BITCOIND_RPC_USERNAME,
        BITCOIND_RPC_PASSWORD,
        BITCOIND_RPC_HOST,
        BITCOIND_RPC_PORT))

  def keep_alive(fun):
    def ping_and_reconnect(self, *args, **kwargs):
      try:
        # Cheap API call that checks wether we're connected
        self.server.help()
      except:
        self.connect()
      return fun(self, *args, **kwargs)
    return ping_and_reconnect

  @keep_alive
  def _get_json_transaction(self, hex_transaction):
    return self.server.decoderawtransaction(hex_transaction)

  @keep_alive
  def sign_transaction(self, raw_transaction, prevtx = "[]"):
    result = self.server.signrawtransaction(raw_transaction, prevtx)
    return result['hex']

  @keep_alive
  def is_valid_transaction(self, raw_transaction):
    # Is raw transaction valid and decodable?
    try:
      transaction = self._get_json_transaction(raw_transaction)
    except ProtocolError:
      return False
    return True

  @keep_alive
  def get_inputs_outputs(self, raw_transaction):
    transaction_dict = self._get_json_transaction(raw_transaction)
    vin = transaction_dict["vin"]
    vouts = transaction_dict["vout"]
    result = (
        sorted([json.dumps({'txid': tx_input['txid'], 'vout':tx_input['vout']}) for tx_input in vin]),
        json.dumps(
            {
              'vout': sorted([
                {
                  "value": vout["value"], 
                  "addresses": vout["scriptPubKey"]["addresses"]
                } for vout in vouts
              ])
            }
        )
    )

    return result

  @keep_alive
  def transaction_already_signed(self, raw_transaction, prevtx):
    signed_transaction = self.sign_transaction(raw_transaction, prevtx)
    if signed_transaction == raw_transaction:
      return True
    return False

  @keep_alive
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

  @keep_alive
  def transaction_contains_output(self, raw_transaction, address, fee):
    transaction_dict = self._get_json_transaction(raw_transaction)
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

  @keep_alive
  def transaction_contains_oracle_fee(self, raw_transaction):
    return self.transaction_contains_output(raw_transaction, ORACLE_ADDRESS, ORACLE_FEE)

  @keep_alive
  def transaction_contains_org_fee(self, raw_transaction):
    return self.transaction_contains_output(raw_transaction, ORGANIZATION_ADDRESS, ORGANIZATION_FEE)

  @keep_alive
  def create_multisig_address(self, min_sigs, keys):
    return self.server.createmultisig(min_sigs, keys)

  @keep_alive
  def add_multisig_address(self, min_sigs, keys):
    return self.server.addmultisigaddress(min_sigs, keys)

  @keep_alive
  def create_multisig_transaction(self, tx_inputs, outputs):
    raw_transaction = self.server.createrawtransaction(json.dumps(tx_inputs), json.dumps(outputs))


