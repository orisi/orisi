
import logging
import json
import hashlib

class BaseHandler:
  def __init__(self, oracle):
    self.oracle = oracle

  def handle_request(self, task):
    raise NotImplementedError()

  def handle_task(self, task):
    raise NotImplementedError()



  def valid_task(self, task):
  	return True

  def is_proper_transaction(self, tx):
    transaction = tx['raw_transaction']
    prevtx = tx['prevtx']

    if not self.oracle.btc.is_valid_transaction(transaction):
      logging.debug("transaction invalid")
      return False

    if len(self.inputs_addresses(prevtx))>1:
      logging.debug("all inputs should come from the same multisig address")
      return False

    if not self.includes_me(prevtx):
      logging.debug("transaction does not include me")
      return False

    if not self.oracle.btc.transaction_contains_org_fee(transaction):
      logging.debug("org fee not found")
      return False

    if not self.oracle.btc.transaction_contains_oracle_fee(transaction):
      logging.debug("oracle fee not found")
      return False

    if self.oracle.btc.transaction_already_signed(transaction, prevtx):
      logging.debug("transaction already signed")
      return False

    return True

  def get_raw_tx_hash(self, raw_transaction, locktime):
    inputs, outputs = self.oracle.get_inputs_outputs(raw_transaction)
    request_dict= {
        "inputs": inputs,
        "outputs": outputs,
        "locktime": locktime,
    }

    return hashlib.sha256(json.dumps(request_dict)).hexdigest()
