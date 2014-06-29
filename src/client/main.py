#!/usr/bin/env python2.7
from collections import defaultdict
from client import OracleClient, PasswordNotMatchingError
import sys
import json

START_COMMAND = "./client.sh"

def unknown(args):
  """unknown operation"""
  print "unknown operation, use {} help for possible operations".format(START_COMMAND)

def __add_multisig(args, blocking):
  if len(args) < 3:
    print "Not enough arguments"
    return
  c = OracleClient()
  client_pubkey = args[0]
  oracle_pubkeys = args[2]
  try:
    number_of_sigs = int(args[1])
  except ValueError:
    print "number_of_sigs must be int"
    return
  try:
    oracle_pubkey_list = json.loads(oracle_pubkeys)
  except ValueError:
    print "pubkey_list not valid json"
    return
  print c.create_multisig_address(client_pubkey, oracle_pubkey_list, number_of_sigs, blocking)


def add_multisig(args):
  """
  Creates and adds multisig address to database.
  Arguments:
  1. Client public key
  2. Number of oracle signatures needed
  3. List of public keys (string, json)
  """
  __add_multisig(args, True)
  print "send bitcoins you want to use to that transaction, then add transaction \
      either with addrawtransaction (hex transaction as argument), or with \
      addtransaction (txid as argument, ONLY IF the transaction was send locally, \
      from your current bitcoind)"

def add_bounty_multisig(args):
  """
  Creates and adds multisig address to database. This address does not need client signatures
  Arguments:
  1. Client public key
  2. Number of oracle signatures needed
  3. List of public keys (string, json)
  """
  __add_multisig(args, False)
  print "send bitcoins you want to use to that transaction, then add transaction \
      with addrawtransaction (hex transaction as argument)"

def describe_protocol(args):
  """Describes how to create full transaction step by step"""
  steps = [
    "Get oracles' public keys as json list",
    "Create address with getmultiaddress ({0} help for more info)".format(START_COMMAND),
    "Send coins you want to lock on that address, save transaction",
    "Use addrawtransaction to save transaction you've created (see more with help)",
    "Prepare request with {0} preparerequest ({0} help for more info)".format(START_COMMAND),
    "Send request with {0} sendrequest".format(START_COMMAND)
  ]
  for idx, step in enumerate(steps):
    print "{}. {}".format(idx+1, step)

def create_transaction(args):
  """
  Creates raw transaction
  Arguments:
  1. Input txids, vout - json of list of elements:
  [{
    "txid": "a93..."
    "vout: 0
  }, ...]
  2. Outputs, json:
  {
    "address1": amount1,
    "address2": amount2,
    ...
  }
  """
  if len(args) < 2:
    print "Not enough arguments"
    return
  c = OracleClient()
  return c.create_multisig_transaction(args[0], args[1])

def create_signed_transaction(args):
  """
  Creates raw transaction and signs it.
  Arguments:
  1. Input txids, vout - json of list of elements:
  [{
    "txid": "a93..."
    "vout: 0
  }, ...]
  2. Outputs, json:
  {
    "address1": amount1,
    "address2": amount2,
    ...
  }
  """
  raw_transaction =  create_transaction(args)
  signed_transaction = OracleClient().sign_transaction(raw_transaction)
  return signed_transaction

def prepare_transaction_request(args):
  try:
    locktime = int(args[0])
  except ValueError:
    print "locktime must be int"
    return
  signed_transaction = args[1]
  prevtx = args[2]
  try:
    condition = args[3]
  except IndexError:
    # For now we do not verify conditions
    condition = "True"
  return OracleClient().prepare_request(signed_transaction, locktime, condition, prevtx)

def send_transaction(args):
  """
  Sends transaction to bitmessage network
  Takes locktime, signed_raw_transaction, condition (optional)
  """
  transaction = prepare_transaction_request(args)
  if not transaction:
    return
  OracleClient().send_transaction(transaction)

def add_raw_transaction(args):
  """
  Adds hex transaction to DB, it will be used later
  to create your multisig transaction.
  """
  if len(args) < 1:
    print "not enough arguments"
    return
  raw_transaction = args[0]
  txid = OracleClient().add_raw_transaction(raw_transaction)
  print txid

def add_oracle(args):
  """
  Adds Oracle to Oracle Database. Takes three arguments
  (pubkey, address, fee).
  """
  if len(args) < 3:
    print "not enough arguments"
    return
  pubkey = args[0]
  address = args[1]
  fee = args[2]
  OracleClient().add_oracle(pubkey, address, fee)

def create_bounty_request(args):
  """
  Creates bounty request that has to be sent to Bitmessage network
  Arguments:
  1. tx_inputs string json
  [
    {
      "txid": "ab45...",
      "vout": 0
    },
    ...
  ] WARNING add raw transaction first with {0} addrawtransaction
  2. return_address string (where the cash should go after locktime if no-one solves riddle)
  3. oracle_ids string json (list of ids of oracles that are part of this transaction,
    oracles are assumed to be taken from standard list (http://oracles.li/list-default.json), if
    no then add oracles with ./client.sh addoracle)
  4. password
  5. locktime
  """
  if len(args) < 5:
    print "not enough arguments"
    return
  try:
    json.loads(args[0])
    json.loads(args[2])
  except ValueError:
    print "tx_inputs and oracle_addresses must be valid jsons"
    return
  try:
    int(args[4])
  except ValueError:
    print "locktime must be int"
    return
  print OracleClient().create_bounty_request(json.loads(args[0]), args[1], json.loads(args[2]), args[3], int(args[4]))


def create_request(args):
  """
  Creates transaction request that has to be sent to Bitmessage network
  Arguments:
  1. tx_inputs string json
  [
    {
      "txid": "ab45...",
      "vout": 0
    },
    ...
  ] WARNING add raw transaction first with {0} addrawtransaction
  2. receiver_address string (for now only one receiver, will get amount-minersfee-oraclesfee)
  3. oracle_addresses string json (list of addresses of oracles that are part of this transaction,
    oracles are assumed to be taken from standard list (http://oracles.li/list-default.json), if
    no then add oracles with {0} addoracle)
  4. locktime
  5. condition (unused, useful in future for complicated tasks)
  """.format(START_COMMAND)
  if len(args) < 4:
    print "not enough arguments"
    return
  try:
    json.loads(args[0])
    json.loads(args[2])
  except ValueError:
    print "tx_inputs and oracle_addresses must be valid jsons"
    return
  try:
    int(args[3])
  except ValueError:
    print "locktime must be int"
    return
  print OracleClient().create_request(json.loads(args[0]), args[1], json.loads(args[2]), int(args[3]))

def list_oracles(args):
  """
  Prints json list of oracles that are currently present in your database
  """
  oracles = json.loads(OracleClient().list_oracles())
  for oracle in oracles:
    print "Id: {} Fee: {} Pubkey: {} Address: {}".format(oracle['id'], oracle['fee'], oracle['pubkey'], oracle['address'])

def get_pubkeys(args):
  """
  Prints json list of oracles by id in arguments
  """
  ids = []
  for arg in args:
    try:
      ids.append(int(arg))
    except ValueError:
      print "id value must be int"
      return
  print OracleClient().get_oracle_pubkeys(ids)

def list_bounties(args):
  """
  Prints json list of all bounties that are currently available
  """
  print OracleClient().list_bounties()

def check_pass(args):
  """
  Checks if given password unlocks given bounty
  Arguments:
  1. pwtxid (string, required) id of bounty
  2. password (string, required) password you want to check
  """
  if len(args) < 2:
    print "not enough arguments"
    return
  pwtxid = args[0]
  password = args[1]
  result = OracleClient().check_pass(pwtxid, password)
  if result:
    print "Your password unlocks bounty. Send it with {} sendbountysolution pwtxid password btc_address".format(START_COMMAND)
  else:
    print "Incorrect password"

def send_bounty_solution(args):
  """
  Sends bounty solution to oracles so they can give you prize
  Arguments:
  1. pwtxid (string, required) id of bounty
  2. password (string, required) password you want to check
  3. btc_address (string, required) your bitcoin address on which you'll receive your money
  """
  if len(args) < 3:
    print "not enough arguments"
    return
  pwtxid = args[0]
  password = args[1]
  address = args[2]
  try:
    OracleClient().send_bounty_solution(pwtxid, password, address)
  except PasswordNotMatchingError:
    print "Your password doesn't match bounty password"
    return

def send_request(args):
  """
  Takes one argument. You can create request with createrequest call
  1. request - string, json
  """
  if len(args) < 1:
    print "not enough arguments"
    return
  try:
    json.loads(args[0])
  except ValueError:
    print "request must be valid json"
    return
  OracleClient().send_transaction(args[0])

def send_bounty_request(args):
  """
  Creates bounty request AND BROADCASTS IT, use createbountyrequest with same arguments to see raw outcome
  Arguments:
  1. tx_inputs string json
  [
    {
      "txid": "ab45...",
      "vout": 0
    },
    ...
  ] WARNING add raw transaction first with {0} addrawtransaction
  2. return_address string (where the cash should go after locktime if no-one solves riddle)
  3. oracle_addresses string json (list of addresses of oracles that are part of this transaction,
    oracles are assumed to be taken from standard list (http://oracles.li/list-default.json), if
    no then add oracles with {0} addoracle)
  4. password
  5. locktime
  """
  if len(args) < 5:
    print "not enough arguments"
    return
  try:
    json.loads(args[0])
    json.loads(args[2])
  except ValueError:
    print "tx_inputs and oracle_addresses must be valid jsons"
    return
  try:
    int(args[4])
  except ValueError:
    print "locktime must be int"
    return
  request = OracleClient().create_bounty_request(json.loads(args[0]), args[1], json.loads(args[2]), args[3], int(args[4]))
  OracleClient().send_bounty_request(request)

RAW_OPERATIONS = {
  'addmultisig': add_multisig,
  'describeprotocol': describe_protocol,
  'addrawtransaction': add_raw_transaction,
  'addoracle': add_oracle,
  'createrequest': create_request,
  'listoracles': list_oracles,
  'getpubkeys': get_pubkeys,
  'listbounties': list_bounties,
  'sendrequest': send_request,
  'checkpass': check_pass,
  'sendbountysolution': send_bounty_solution,
  'addbountyaddress': add_bounty_multisig,
  'createbountyrequest': create_bounty_request,
  'sendbountyrequest': send_bounty_request,
}
OPERATIONS = defaultdict(lambda:unknown, RAW_OPERATIONS)

SHORT_DESCRIPTIONS = {
  'addmultisig': "(client_pubkey, required_signatures, json_list_of_oracle_pubkeys) creates and adds multisig address to database and bitcoind, needed to create transaction request",
  'addbountyaddress': "Same as addmultisig, but will create bounty address, which will be non-blocking - use this function for password transaction",
  'describeprotocol': "describes step by step how to create transaction request",
  'addrawtransaction': "(hextransaction) adds transaction to database, all transactions used later as input must be added that way",
  'addoracle': "(pubkey, address, fee) manualy add oracle to database",
  'listoracles': "lists all available oracles",
  'getpubkeys': "(oracle_id1, oracle_id2, ...) returns json list of oracles pubkeys",
  'createrequest': "(tx_inputs, receiver_address, oracle_addresses, locktime, condition) - creates json request",
  'sendrequest': "sends request to oracles via Bitmessage network",
  'listbounties': "lists all available bounties",
  'checkpass': "checks password for given bounty",
  'sendbounty': "sends bounty solution to oracles",
  'createbountyrequest': "(tx_inputs, return_address, oracle_addresses, password, locktime)",
  'sendbountyrequest': "sends request to oracles via Bitmessage network",
}


def help():
  print "You can use one of the following functions:"
  for name, desc in SHORT_DESCRIPTIONS.iteritems():
    print "{0} - {1}".format(name, desc)
  print "Learn more by using {0} help functionname".format(START_COMMAND)

def help_fun(fun_name):
  fun = OPERATIONS[fun_name]
  print fun.__doc__

def main(args):
  if len(args) == 0:
    print "no arguments given, use {0} help for possible operations".format(START_COMMAND)
    return
  if args[0] == 'help':
    if len(args) == 1:
      help()
    else:
      help_fun(args[1])
    return
  operation = OPERATIONS[args[0]]
  #special case
  operation(args[1:])


if __name__=="__main__":
  args = sys.argv[1:]
  main(args)
