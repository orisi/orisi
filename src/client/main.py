#!/usr/bin/env python2.7
from collections import defaultdict
from client import OracleClient, PasswordNotMatchingError
import sys
import json
import hashlib
import time

from shared import liburl_wrapper

from math import ceil
from random import randrange

from shared.bitcoind_client.bitcoinclient import BitcoinClient
from shared.bitmessage_communication.bitmessageclient import BitmessageClient

START_COMMAND = "./client.sh"

def unknown(args):
  """unknown operation"""
  print "unknown operation, use {} help for possible operations".format(START_COMMAND)


CHARTER_URL = 'http://oracles.li/bounty-charter.json'

def main(args):

  btc = BitcoinClient()
  tmp_address = btc.validate_address(btc.get_new_address())

#  print btc.validate_address('1BcEDbcYXfZXaVJh2WeCbc3TnEU37eRPSt')

  charter_json = liburl_wrapper.safe_read(CHARTER_URL, timeout_time=10)
  charter = json.loads(charter_json)

  print "temp pubkey: %r" % tmp_address['pubkey']
  print "charter: %r" % charter

#  c = OracleClient()
  client_pubkey = tmp_address['pubkey']
  oracle_pubkeys = []
  for o in charter['nodes']:
    oracle_pubkeys.append(o['pubkey'])

  min_sigs = int(ceil(float(len(oracle_pubkeys))/2))

  key_list = [client_pubkey] + oracle_pubkeys

  print "min_sigs: %r" % min_sigs
  print "keys_list: %r" % key_list


  print "-------"

  response = btc.create_multisig_address(min_sigs, key_list)

  print "%r" % response

  print btc.validate_address(response['address'])


def prepare_password_hash(password):
    DIFFICULTY = 1000000000
    rn = randrange(DIFFICULTY/100, DIFFICULTY) 
    salted_password = "{}#{}".format(password, rn)
    hashed = hashlib.sha512(salted_password).hexdigest()
    return hashed

def main2(args):

  request = {}

  btc = BitcoinClient()
  charter_json = liburl_wrapper.safe_read(CHARTER_URL, timeout_time=10)
  charter = json.loads(charter_json)

  client_pubkey = '03a9f6c8107a174f451fc7101e95fd1e1003d2b435d94b80b7ff8ebfbfba1841b7'
  oracle_pubkeys = []
  oracle_fees = {}
  oracle_bms = []

  for o in charter['nodes']:
    oracle_pubkeys.append(o['pubkey'])
    oracle_fees[o['address']] = o['fee']
    oracle_bms.append(o['bm'])
    oracle_bms.append(o['bm'])

  oracle_fees[charter['org_address']] = charter['org_fee']

  min_sigs = int(ceil(float(len(oracle_pubkeys))/2))

  key_list = [client_pubkey] + oracle_pubkeys

  response = btc.create_multisig_address(min_sigs, key_list)
  msig_addr = response['address'] # we're using this as an identificator

  request['message_id'] = "%s%s-" % (msig_addr, str(randrange(1000000000,9000000000)))

  ###

  request['pubkey_json'] = key_list
  request['miners_fee'] = 0.0001

  prevtx = {

    'redeemScript' : '52210281cf9fa9241f0a9799f27a4d5d60cff74f30eed1d536bf7a72d3dec936c151632102e8e22190b0adfefd0962c6332e74ab68831d56d0bfc2b01b32beccd56e3ef6f02103a9bd3bfbd9f9b1719d3ecad8658796dc5e778177d77145b5c37247eb306086182103a9f6c8107a174f451fc7101e95fd1e1003d2b435d94b80b7ff8ebfbfba1841b754ae',
    'scriptPubKey' : 'a91412d857a1778be8ad4b2e548a2632aac14f3063a587',
    'vout':0,
    'txid':'8b5eb0ea6a9bbbf7ecec66edb5d6b9e10cdf9e6ebe6f9bee35d630817b2fbce3',

  }

  request['prevtx'] = [ prevtx ]
  request['password_hash'] = prepare_password_hash('satoshi')
  request["req_sigs"] = min_sigs
  request['operation'] = 'bounty_create'
  request['sum_amount'] = 0.002
  request['locktime'] = 1405418400
  request['return_address'] = '1MGqtD59cwDGpJww2nugDKUiT2q81fxT5A'
  request['oracle_fees'] = oracle_fees

  bm = BitmessageClient()
  print "sending: %r" % json.dumps(request)
  print bm.chan_address

  request_content = json.dumps(request)

  print bm.send_message(bm.chan_address, "bounty_create", request_content)

  print ""
  print '''Gathering oracle responses. If it's your first time using this Bitmessage address, it may take even an hour to few hours before the network
  forwards your message and you get the replies. All the future communication should be faster and come within single minutes. [this message may be inaccurate, todo for: @gricha]'''
  print ""

  msg_count = 0

  while oracle_bms:
    messages = bm.get_unread_messages()
    print "unread messages: %r" % len(messages)
    for msg in messages:
      if msg.from_address in oracle_bms:
        try:
          content = json.loads(msg.message)
        except:
          print msg.message
          print 'failed decoding message'
          continue

        if content['message_id'] == request['message_id']:
            print "[%r][%r] %r" % (msg.subject, msg.from_address, msg.message)
            print ""
            oracle_bms.remove(msg.from_address)

    if oracle_bms:
      print "waiting..."
      time.sleep(5)

    print "done"



  ####
  '''
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
    pubkey_list = json.loads(multisig_info['pubkey_json'])

    prevtx = self.prepare_prevtx(tx_inputs)
    message = json.dumps({
      "operation": "bounty_create",
      "locktime": locktime,
      "pubkey_json": pubkey_list,
      "req_sigs": req_sigs,
      "sum_amount": float(amount),
      "miners_fee": float(MINERS_FEE),
      "prevtx": prevtx,
      "oracle_fees": oracle_fees,
      "password_hash": pass_hash,
      "return_address": return_address
    })
    return message
'''

#  MultisigRedeemDb(self.db).save({
#      "multisig": response['address'],
#      "min_sig": real_min_sigs,
#      "redeem_script": response['redeemScript'],
#      "pubkey_json": json.dumps(sorted(key_list))})

#  self.btc.add_multisig_address(real_min_sigs, key_list)
#  return response


#  oracle_list = oracle_list['nodes']

#  for oracle in oracle_list:

#    self.add_oracle(oracle['public_key'], oracle['address'], oracle['fee'])


#  oracles = json.loads(OracleClient().list_oracles())
#  for oracle in oracles:
#    print "Id: {} Fee: {} Pubkey: {} Address: {}".format(oracle['id'], oracle['fee'], oracle['pubkey'], oracle['address'])

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
  'main': main,
  'main2': main2,
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
  'main': "main",
  'main2': "main2",
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
