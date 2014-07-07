
import json
import hashlib

class BaseHandler:
  def __init__(self, oracle):
    self.oracle = oracle
    self.btc = oracle.btc

  def handle_request(self, task):
    raise NotImplementedError()

  def handle_task(self, task):
    raise NotImplementedError()



  def valid_task(self, task):
  	return True

  def get_tx_hash(self, tx):
    inputs, outputs = self.btc.get_inputs_outputs(tx)
    request_dict= {
        "inputs": inputs,
        "outputs": outputs,
    }

    return hashlib.sha256(json.dumps(request_dict)).hexdigest()
