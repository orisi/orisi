import json

from Crypto.PublicKey import RSA
from decimal import Decimal

class Util:
  @staticmethod
  def construct_key_from_data(rsa_data):
    k = json.loads(rsa_data['whole'])
    key = RSA.construct((
        long(k['n']),
        long(k['e']),
        long(k['d']),
        long(k['p']),
        long(k['q']),
        long(k['u'])))
    return key

  @staticmethod
  def construct_pubkey_from_data(rsa_data):
    key = RSA.construct((
        long(rsa_data['n']),
        long(rsa_data['e'])))
    return key

  @staticmethod
  def create_future_transaction(btc, prevtx, outputs, amount_available, receiver_address, locktime):
    inputs = []
    for tx in prevtx:
      inputs.append({'txid': tx['txid'], 'vout': tx['vout']})
    cash_back = amount_available
    for oracle, fee in outputs.iteritems():
      cash_back -= Decimal(fee)

    outputs[receiver_address] = cash_back

    vout = {}
    for address, value in outputs.iteritems():
      # My heart bleeds when I write it
      vout[address] = float(value)

    transaction = btc.create_multisig_transaction(inputs, vout)
    return transaction
