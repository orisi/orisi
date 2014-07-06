import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import base64
import hashlib
import time
import json
import logging

from Crypto.PublicKey import RSA
from decimal import Decimal, getcontext
from random import randrange

from shared.bitcoind_client.bitcoinclient import BitcoinClient
from shared.bitmessage_communication.bitmessageclient import BitmessageClient
from shared import liburl_wrapper
from client_db import (
    ClientDb,
    SignatureRequestDb,
    MultisigRedeemDb,
    RawTransactionDb,
    OracleListDb,
    OracleCheckDb,
    BountyAvailable,
    HashGuessed)

URL_ORACLE_LIST = 'http://oracles.li/list-default.json'
MINIMUM_DIFFERENCE = 3600 # in seconds
DIFFICULTY = 1000000000

# Fixed for now, TODO: get better estimation of how big fee should be
MINERS_FEE = "0.0001"

class OracleMissingError(Exception):
  pass

class PasswordNotMatchingError(Exception):
  pass

class UnsupportedTransactionError(Exception):
  pass

class AddressMissingError(Exception):
  pass

class TransactionUnknownError(Exception):
  pass

class NoInputsError(Exception):
  pass

class TooSmallAmountError(Exception):
  pass

class OracleClient:
  def __init__(self):
    getcontext().prec=8
    self.btc = BitcoinClient()
    self.bm = BitmessageClient()
    self.db = ClientDb()
    self.update_oracle_list()

    self.operations = {
        'new_bounty': self.new_bounty,
    }
    self.read_messages()

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

  def new_bounty(self, msg):
    body = json.loads(msg.message)
    pwtxid = body['pwtxid']
    hsh = body['password_hash']

    rsa_pubkey = body['rsa_pubkey']
    req_sigs = body['req_sigs']
    BountyAvailable(self.db).update_pwtxid(pwtxid, hsh, rsa_pubkey, req_sigs)

  def handle_message(self, msg):
    try:
      body = json.loads(msg.message)
    except ValueError:
      logging.info('message doesnt contain json')
      return

    if not 'operation' in body:
      logging.info('body doesnt have operation')
      return

    operation = body['operation']
    if not operation in self.operations:
      return
    func = self.operations[operation]
    func(msg)

  def read_messages(self):
    messages = self.bm.get_unread_messages()
    for msg in messages:
      self.handle_message(msg)
      self.bm.mark_message_as_read(msg)

  def create_multisig_address(self, client_pubkey, oracle_pubkey_list, min_sigs, blocking=True):
    """
    Creates multisig address between client and oracles.
    blocking is responsible for creating either address, that requires many client
    signatures (low trust for oracles), or only one signature (high trust for oracle).
    One signature is required only for address to be unique.
    client_pubkey should be choosen freshly every time
    """
    if blocking:
      max_sigs = len(oracle_pubkey_list)
      difference = max_sigs - min_sigs

      real_min_sigs = max_sigs + 1
      client_sig_number = difference + 1
    else:
      real_min_sigs = min_sigs
      client_sig_number = 1

    key_list = [client_pubkey for _ in range(client_sig_number)] + oracle_pubkey_list
    response = self.btc.create_multisig_address(real_min_sigs, key_list)

    MultisigRedeemDb(self.db).save({
        "multisig": response['address'],
        "min_sig": real_min_sigs,
        "redeem_script": response['redeemScript'],
        "pubkey_list": json.dumps(sorted(key_list))})

    self.btc.add_multisig_address(real_min_sigs, key_list)
    return response

  def create_multisig_transaction(self, input_txids, outputs):
    transaction_hex = self.btc.create_multisig_transaction(input_txids, outputs)
    return transaction_hex

  def sign_transaction(self, hex_transaction, prevtx=[]):
    signed_hex_transaction = self.btc.sign_transaction(hex_transaction, prevtx)
    return signed_hex_transaction

  def prepare_request(self, transaction, locktime, condition, prevtx, pubkey_list, req_sigs):
    message = json.dumps({
      "operation": "conditioned_transaction",
      "transactions": [
        {
          "raw_transaction": transaction,
          "prevtx": prevtx,
        }
      ],
      "locktime": locktime,
      "condition": condition,
      "pubkey_list": pubkey_list,
      "req_sigs": req_sigs
    })
    return message

  def save_transaction(self, request):
    try:
      json.loads(request)
    except ValueError:
      logging.error("request is invalid JSON")
      return
    SignatureRequestDb(self.db).save({"json_data": request})

  def send_transaction(self, request):
    self.save_transaction(request)
    self.bm.send_message(self.bm.chan_address, "conditioned_transaction", request)

  def send_bounty_request(self, request):
    self.bm.send_message(self.bm.chan_address, "password_transaction", request)

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
    # TODO: check if pubkey is valid and corresponding to address, check if fee is valid
    OracleListDb(self.db).save({
        "pubkey": pubkey,
        "address": address,
        "fee": fee})

  def get_amount_from_inputs(self, raw_tx_inputs):
    amount = Decimal("0")

    # Filters duplicates - can't use sets - dict is unhashable
    tx_inputs = []
    for tx in raw_tx_inputs:
      if tx not in tx_inputs:
        tx_inputs.append(tx)

    for tx in tx_inputs:
      raw_transaction = RawTransactionDb(self.db).get_tx(tx['txid'])
      if not raw_transaction:
        raise TransactionUnknownError()
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

  def get_oracles_by_ids(self, oracle_ids):
    oracles = OracleListDb(self.db).get_oracles_by_ids(oracle_ids)
    if len(oracles) != len(oracle_ids):
      raise OracleMissingError()
    return oracles

  def prepare_prevtx(self, prevtxs):
    for tx in prevtxs:
      raw_transaction = RawTransactionDb(self.db).get_tx(tx['txid'])
      if not raw_transaction:
        raise TransactionUnknownError()
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
          tx['scriptPubKey'] = v['scriptPubKey']['hex']
          break
    return prevtxs

  def get_address(self, tx):
    raw_transaction = RawTransactionDb(self.db).get_tx(tx['txid'])
    if not raw_transaction:
      raise TransactionUnknownError()
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

  def create_request(
      self,
      tx_inputs,
      receiver_address,
      oracle_addresses,
      locktime=0,
      condition="True"):

    if len(tx_inputs) == 0:
      raise NoInputsError()

    amount = self.get_amount_from_inputs(tx_inputs)
    oracles = self.get_oracles(oracle_addresses)

    # First let's substract what's going on fees
    amount -= Decimal(MINERS_FEE)

    outputs = {}
    for oracle in oracles:
      if not oracle['address'] in outputs:
        outputs[oracle['address']] = 0
      outputs[oracle['address']] += float(oracle['fee'])
      amount -= Decimal(oracle['fee'])

    if amount <= Decimal('0'):
      raise TooSmallAmountError()

    if receiver_address not in outputs:
      outputs[receiver_address] = 0
    outputs[receiver_address] += float(amount)

    raw_transaction = self.create_multisig_transaction(tx_inputs, outputs)

    prevtx = self.prepare_prevtx(tx_inputs)
    signed_transaction = self.sign_transaction(raw_transaction, prevtx)

    multisig_info = self.get_address(tx_inputs[0])
    req_sigs = multisig_info['min_sig']
    pubkey_list = json.loads(multisig_info['pubkey_list'])

    # Now we have all we need to create proper request
    return self.prepare_request(
        signed_transaction,
        locktime,
        condition,
        prevtx,
        pubkey_list,
        req_sigs)

  def get_password_hash(self, password):
    rn = randrange(DIFFICULTY)
    salted_password = "{}#{}".format(password, rn)
    hashed = hashlib.sha512(salted_password).hexdigest()
    return hashed

  def create_bounty_request(
      self,
      tx_inputs,
      return_address,
      oracle_ids,
      password,
      locktime):
    if len(tx_inputs) == 0:
      raise NoInputsError()

    amount = self.get_amount_from_inputs(tx_inputs)
    oracles = self.get_oracles_by_ids(oracle_ids)
    oracle_fees = {}
    for oracle in oracles:
      oracle_fees[oracle['address']] = oracle['fee']

    pass_hash = self.get_password_hash(password)

    multisig_info = self.get_address(tx_inputs[0])
    req_sigs = multisig_info['min_sig']
    pubkey_list = json.loads(multisig_info['pubkey_list'])

    prevtx = self.prepare_prevtx(tx_inputs)
    message = json.dumps({
      "operation": "password_transaction",
      "locktime": locktime,
      "pubkey_list": pubkey_list,
      "req_sigs": req_sigs,
      "sum_amount": float(amount),
      "miners_fee": float(MINERS_FEE),
      "prevtx": prevtx,
      "oracle_fees": oracle_fees,
      "password_hash": pass_hash,
      "return_address": return_address
    })
    return message

  def list_oracles(self):
    oracles = OracleListDb(self.db).get_all_oracles()
    return json.dumps(oracles)

  def get_oracle_pubkeys(self, oracle_ids):
    oracles = OracleListDb(self.db).get_all_oracles()
    oracles = [o['pubkey'] for o in oracles if o['id'] in oracle_ids]
    return json.dumps(oracles)

  def list_bounties(self):
    bounties = BountyAvailable(self.db).get_all_available()
    return json.dumps(bounties)

  def check_pass(self, pwtxid, pwd):
    ba = BountyAvailable(self.db).get_by_pwtxid(pwtxid)
    hg = HashGuessed(self.db).get_by_pwtxid(pwtxid)

    if hg:
      hashed = "{}#{}".format(pwd, hg['number'])
      hashed = hashlib.sha512(hashed).hexdigest()
      if ba['hash'] == hashed:
        return True

    i = 0
    while i < DIFFICULTY:
      i += 1
      salted = "{}#{}".format(pwd, i)
      new_hash = hashlib.sha512(salted).hexdigest()
      if new_hash == ba['hash']:
        HashGuessed(self.db).save({"pwtxid":pwtxid,"password":pwd,"number":i})
        return True
    return False

  def get_number(self, pwtxid):
    hg = HashGuessed(self.db).get_by_pwtxid(pwtxid)
    if hg:
      return hg['number']

  def prepare_bounty_request(self, pwtxid, passwords):
    message = json.dumps({
        'operation': 'bounty_redeem',
        'pwtxid': pwtxid,
        'passwords': passwords
    })
    return message

  def construct_pubkey_from_data(self, rsa_data):
    key = RSA.construct((
        long(rsa_data['n']),
        long(rsa_data['e'])))
    return key

  def send_bounty_solution(self, pwtxid, pwd, address):
    if not self.check_pass(pwtxid, pwd):
      raise PasswordNotMatchingError()

    ba = BountyAvailable(self.db).get_by_pwtxid(pwtxid)
    keys = json.loads(ba['current_keys_json'])

    passwords = {}

    number = self.get_number(pwtxid)

    pass_hash = hashlib.sha512("{}#{}".format(pwd, number)).hexdigest()

    msg = json.dumps({
      "pass_hash": pass_hash,
      "address": address
    })
    for key in keys:
      rsa_key = self.construct_pubkey_from_data(key)
      base64_msg = base64.encodestring(rsa_key.encrypt(msg, 0)[0])
      rsa_hash = hashlib.sha256(json.dumps(key)).hexdigest()
      passwords[rsa_hash] = base64_msg
    request = self.prepare_bounty_request(pwtxid, passwords)
    self.bm.send_message(self.bm.chan_address, "bounty_redeem", request)
