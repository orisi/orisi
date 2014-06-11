import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import hashlib
import json
import logging

from shared.bitcoind_client.bitcoinclient import BitcoinClient
from shared.bitmessage_communication.bitmessageclient import BitmessageClient
from client_db import (
    ClientDb, 
    SignatureRequestDb, 
    MultisigRedeemDb,
    RawTransactionDb)

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

    MultisigRedeemDb(self.db).save({
        "multisig": response['address'], 
        "min_sig": real_min_sigs,
        "redeem_script": response['redeemScript'],
        "pubkey_json": json.dumps(sorted(key_list))})

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

  def save_transaction(self, request):
    try:
      raw_request = json.loads(request)
    except ValueError:
      logging.error("request is invalid JSON")
      return
    prevtx = json.dumps(raw_request['prevtx'])
    prevtx_hash = hashlib.sha256(prevtx).hexdigest()
    SignatureRequestDb(self.db).save({"prevtx_hash": prevtx_hash, "json_data": request})

  def send_transaction(self, request):
    self.save_transaction(request)
    self.bm.send_message(self.bm.chan_address, "TransactionRequest", request)

  def add_raw_transaction(self, raw_transaction):
    if not self.btc.is_valid_transaction(raw_transaction):
      logging.error("hex transaction is not valid transaction")
    transaction_json = self.btc._get_json_transaction(raw_transaction)
    txid = transaction_json['txid']
    RawTransactionDb(self.db).save({
        "txid": txid,
        "raw_transaction": raw_transaction})
