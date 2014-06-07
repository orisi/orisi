from settings_local import (
    BITCOIND_RPC_USERNAME,
    BITCOIND_RPC_PASSWORD,
    BITCOIND_RPC_HOST,
    BITCOIND_RPC_PORT,)

import json
import jsonrpclib

import decimal
import jsonrpclib


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
  def sign_transaction(self, raw_transaction):
#    result = self.server.signrawtransaction(transaction, [], ORACLE_PRIVATE_KEY)
    return result['hex']

  @keep_alive
  def is_valid_transaction(self, raw_transaction):
    result = self.server.signrawtransaction(transaction, [], [])
    return result['complete'] == 1

  @keep_alive
  def get_inputs_outputs(self, raw_transaction):
    transaction = self._get_json_transaction(raw_transaction)
    transaction_dict = json.loads(transaction)
    vin = transaction_dict["vin"]
    vouts = transaction_dict["vout"]
    result = {
      "vin_txid": [tx_input["txid"] for tx_input in vin]
      "vout": [
        {
          "value": vout["value"],
          "addresses": vout["scriptPubKey"]["addresses"]
        }
        for vout in vouts
      ]
    }

    return json.dumps(results)

  @keep_alive
  def get_multisig_sender_address(self, transaction):
    #TODO: transaction as it's input should have multisig transaction,
    # This method should get it (i tried to figure it out and don't know how)
    # http://bitcoin.stackexchange.com/questions/7838/why-does-gettransaction-report-me-only-the-receiving-address
    return "3aabb"

  @keep_alive
  def transaction_already_signed(self, transaction):
    #TODO: IF I'VE ALREADY SIGNED THAT TRANSACTION AND NO MORE SIGNATURES ARE REQUIRED FROM ME
    # RETURN FALSE, IN OTHER CASE RETURN TRUE
    return False
