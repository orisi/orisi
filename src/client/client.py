import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import json

from shared.bitcoind_client.bitcoinclient import BitcoinClient
from shared.bitmessage_communication.bitmessageclient import BitmessageClient
from client_db import ClientDb

class OracleClient:
  def __init__(self):
    self.btc = BitcoinClient()
    self.bm = BitmessageClient()
    self.db = ClientDb()

  def create_multisig_address(self, client_pubkey, oracle_pubkey_list_json, min_sigs):
    oracle_pubkey_list = json.loads(oracle_pubkey_list_json)
    max_sigs = len(oracle_pubkey_list)
    difference = max_sigs - min_sigs

    real_min_sigs = max_sigs + 1
    client_sig_number = difference + 1

    key_list = [client_pubkey for _ in range(client_sig_number)] + oracle_pubkey_list
    response = self.btc.create_multisig_address(real_min_sigs, key_list)
    self.btc.server.addmultisigaddress(real_min_sigs, key_list)
    return response

  def create_multisig_transaction(self, input_txids, outputs):
    transaction_hex = self.btc.create_transaction(input_txids, outputs)
    return transaction_hex

  def sign_transaction(self, hex_transaction):
    signed_hex_transaction = self.btc.sign_transaction(hex_transaction)
    return signed_hex_transaction

  def prepare_request(self, transaction, locktime, condition, prevtx):
    message = json.dumps({
      "operation": "transaction",
      "raw_transaction": signed_transaction,
      "locktime": locktime,
      "condition": condition,
      "prevtx": prevtx
    })
    return message

  def send_transaction(self, request):
    self.bm.send_message(self.bm.chan_address, "TransactionRequest", request)
