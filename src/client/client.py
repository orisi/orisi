import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import time
import hashlib
import json
import logging

from decimal import Decimal, getcontext

from shared.bitcoind_client.bitcoinclient import BitcoinClient
from shared.bitmessage_communication.bitmessageclient import BitmessageClient
from shared import liburl_wrapper
from client_db import (
    ClientDb,
    SignatureRequestDb,
    MultisigRedeemDb,
    RawTransactionDb,
    OracleListDb,
    OracleCheckDb)

URL_ORACLE_LIST = 'http://oracles.li/list-default.json'
MINIMUM_DIFFERENCE = 3600 # in seconds

# Fixed for now, TODO: get better estimation of how big fee should be
MINERS_FEE = "0.0001"

class OracleMissingError(Exception):
  pass

class UnsupportedTransactionError(Exception):
  pass

class AddressMissingError(Exception):
  pass

class OracleClient:
  def __init__(self):
    getcontext().prec=8
    self.btc = BitcoinClient()
    self.bm = BitmessageClient()
    self.db = ClientDb()
    self.update_oracle_list()

  def update_oracle_list(self):
    last_check = OracleCheckDb(self.db).get_last()
    current_time = int(time.time())
    if last_check:
      last_time = int(last_check['last_check'])
    else:
      last_time = 0
    if current_time - last_time  > MINIMUM_DIFFERENCE:
      content = liburl_wrapper.safe_read(URL_ORACLE_LIST, timeout_time=10)
      try:
        oracle_list = json.loads(content)
        oracle_list = oracle_list['nodes']
        for oracle in oracle_list:
          self.add_oracle(oracle['public_key'], oracle['address'], oracle['fee'])
      except ValueError:
        logging.error("oracle list json invalid")
      OracleCheckDb(self.db).save({"last_check": current_time})


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
    transaction_hex = self.btc.create_multisig_transaction(input_txids, outputs)
    return transaction_hex

  def sign_transaction(self, hex_transaction, prevtx=[]):
    signed_hex_transaction = self.btc.sign_transaction(hex_transaction, prevtx)
    return signed_hex_transaction

  def prepare_request(self, transaction, locktime, condition, prevtx, pubkey_list, req_sigs):
    message = json.dumps({
      "operation": "transaction",
      "transactions": [
        {
          "raw_transaction": transaction,
          "prevtx": prevtx,
        }
      ],
      "locktime": locktime,
      "condition": condition,
      "pubkey_json": pubkey_list,
      "req_sigs": req_sigs
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
    return txid

  def add_oracle(self, pubkey, address, fee):
    OracleListDb(self.db).save({
        "pubkey": pubkey,
        "address": address,
        "fee": fee})

  def get_amount_from_inputs(self, tx_inputs):
    amount = Decimal("0")
    for tx in tx_inputs:
      raw_transaction = RawTransactionDb(self.db).get_tx(tx['txid'])
      if not raw_transaction:
        print "transaction {0} is not in database, \
            please add transaction with python main.py addtransaction"
        return
      transaction_dict = self.btc._get_json_transaction(raw_transaction['raw_transaction'])
      vouts = transaction_dict['vout']
      for v in vouts:
        if v['n'] == tx['vout']:
          amount += Decimal(v['value'])
          break
    return amount

  def get_oracles(self, oracle_addresses):
    oracles = OracleListDb(self.db).get_oracles(oracle_addresses)
    if len(oracles) != len(oracle_addresses):
      raise OracleMissingError()
    return oracles

  def get_scripts_from_inputs(self, tx_inputs):
    prevtxs = tx_inputs
    for tx in prevtxs:
      raw_transaction = RawTransactionDb(self.db).get_tx(tx['txid'])
      if not raw_transaction:
        print "transaction {0} is not in database, \
            please add transaction with python main.py addtransaction"
        return
      transaction_dict = self.btc._get_json_transaction(raw_transaction['raw_transaction'])
      vouts = transaction_dict['vout']
      for v in vouts:
        if v['n'] == tx['vout']:
          tx['scriptPubKey'] = v['scriptPubKey']['hex']
          break
    return prevtxs

  def get_redeem(self, prevtxs):
    for tx in prevtxs:
      raw_transaction = RawTransactionDb(self.db).get_tx(tx['txid'])
      if not raw_transaction:
        print "transaction {0} is not in database, \
            please add transaction with python main.py addtransaction"
        return
      transaction_dict = self.btc._get_json_transaction(raw_transaction['raw_transaction'])
      vouts = transaction_dict['vout']
      for v in vouts:
        if v['n'] == tx['vout']:
          addresses = v['scriptPubKey']['addresses']
          if len(addresses) != 1:
            raise UnsupportedTransactionError()
          address = addresses[0]
          addr_info = MultisigRedeemDb(self.db).get_address(address)
          if not addr_info:
            raise AddressMissingError()
          tx['redeemScript'] = addr_info['redeem_script']
          break
    return prevtxs

  def get_address(self, tx):
    raw_transaction = RawTransactionDb(self.db).get_tx(tx['txid'])
    if not raw_transaction:
      print "transaction {0} is not in database, \
          please add transaction with python main.py addtransaction"
      return
    transaction_dict = self.btc._get_json_transaction(raw_transaction['raw_transaction'])
    vouts = transaction_dict['vout']
    for v in vouts:
      if v['n'] == tx['vout']:
        addresses = v['scriptPubKey']['addresses']
        if len(addresses) != 1:
          raise UnsupportedTransactionError()
        address = addresses[0]
        addr_info = MultisigRedeemDb(self.db).get_address(address)
        if not addr_info:
          raise AddressMissingError()
        return addr_info

  def create_request(self, tx_inputs, receiver_address, oracle_addresses, locktime=0, condition="True"):
    if len(tx_inputs) == 0:
      print "you need to provide at least one input"
      return

    amount = self.get_amount_from_inputs(tx_inputs)
    try:
      oracles = self.get_oracles(oracle_addresses)
    except OracleMissingError:
      print "one of the oracles you specified is not in database, add it by hand with python main.py addoracle"
      return

    # First let's substract what's going on fees
    amount -= Decimal(MINERS_FEE)

    outputs = {}
    for oracle in oracles:
      outputs[oracle['address']] = float(oracle['fee'])
      amount -= Decimal(oracle['fee'])

    if amount <= Decimal('0'):
      print "tx inputs value is lesser than fees"
      return

    outputs[receiver_address] = float(amount)

    raw_transaction = self.create_multisig_transaction(tx_inputs, outputs)

    prevtx = self.get_scripts_from_inputs(tx_inputs)
    try:
      prevtx = self.get_redeem(prevtx)
    except UnsupportedTransactionError:
      print "one of inputs has more than one address in outputs, unsupported"
      return
    except AddressMissingError:
      print "one of addresses from inputs is not in address database, add multisig \
          address with python main.py getmultiaddress"
      return

    signed_transaction = self.sign_transaction(raw_transaction, prevtx)

    multisig_info = self.get_address(tx_inputs[0])
    req_sigs = multisig_info['min_sig']
    pubkey_list = json.loads(multisig_info['pubkey_json'])

    # Now we have all we need to create proper request
    return self.prepare_request(
        signed_transaction,
        locktime,
        condition,
        prevtx,
        pubkey_list,
        req_sigs)

  def list_oracles(self):
    oracles = OracleListDb(self.db).get_all_oracles()
    return json.dumps(oracles)

