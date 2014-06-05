import json

class BitcoinClient:
  def __init__(self):
    self.connect()

  def connect(self):
    #do some connections here
    pass

  def sing_transaction(self, transaction):
    #TODO: SIGN_TRANSACTION RETURN: NEW SIGNED TRANSACTION
    return transaction

  def is_valid_transaction(self, transaction):
    #TODO: if transaction is valid (it is in fact a transaction and not a stupid string or so)
    return True

  def get_inputs_outputs(self, transaction):
    #TODO: Assumes to get inputs and outputs for transaction
    #PLS GIMME JSON
    return json.dumps({"placeholder":"hehe"})

  def get_multisig_sender_address(self, transaction):
    #TODO: transaction as it's input should have multisig transaction,
    # This method should get it (i tried to figure it out and don't know how)
    # http://bitcoin.stackexchange.com/questions/7838/why-does-gettransaction-report-me-only-the-receiving-address
    return "3aabb"