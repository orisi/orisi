# Main Oracle file

from oracle_db import OracleDb, TaskQueue, KeyValue
from handlers.handlers import op_handlers

from settings_local import ORACLE_ADDRESS, ORACLE_FEE
from shared.bitcoind_client.bitcoinclient import BitcoinClient
from shared.fastproto import(
    generateKey,
    broadcastMessage,
    getMessages)

import json

from handlers.transactionsigner import TransactionSigner

import time
import logging

from decimal import Decimal

# 3 minutes between oracles should be sufficient
HEURISTIC_ADD_TIME = 60 * 3

class FastcastMessage:
  def __init__(self, req):
    body = json.loads(req['body'])

    self.from_address = req['source']
    self.received_time = int(req['epoch'])
    if 'message_id' in body:
      self.msgid = body['message_id']
    else:
      self.msgid = ''

    # Deprecated
    self.subject = "DEPRECATED: DONT USE SUBJECT"
    self.message = req['body']

class MissingOperationError(Exception):
  pass

# Number of confirmations needed for block to get noticed by Oracle
CONFIRMATIONS = 3

class FastcastProtocolError(Exception):
  pass

class Oracle:
  def __init__(self):

    self.db = OracleDb()
    self.btc = BitcoinClient()
    self.kv = KeyValue(self.db)

    self.task_queue = TaskQueue(self.db)

    self.handlers = op_handlers
    self.signer = TransactionSigner(self)

    last_received = self.kv.get_by_section_key('fastcast', 'last_epoch')
    if not last_received:
      self.kv.store('fastcast', 'last_epoch', {'last':0})

    if not self.kv.exists('fastcast', 'address'):
      pub, priv = generateKey()
      self.kv.store('fastcast', 'address', {"pub": pub, "priv": priv})

    logging.info('fastcast pubkey: %r' % self.kv.get_by_section_key('fastcast', 'address')['pub'])

  def broadcast_with_fastcast(self, message):
    data = self.kv.get_by_section_key('fastcast', 'address')
    pub = data['pub']
    priv = data['priv']

    broadcastMessage(message, pub, priv)

  def handle_request(self, request):
    logging.debug(request)
    operation, message = request

    if not operation in self.handlers:
      logging.debug("operation {} not supported".format(operation))
      return

    handler = self.handlers[operation]

    try:
      message.message = json.loads(message.message)
      if 'message_id' in message.message:
        logging.info('parsing message_id: %r' % message.message['message_id'])
      handler(self).handle_request(message)
    except:
      logging.debug(message)
      logging.exception('error handling the request')


    # Save object to database for future reference
    db_class = self.db.operations[operation]
    if db_class:
      db_class(self.db).save(message)

  def get_last_block_number(self):
    val = KeyValue(self.db).get_by_section_key('blocks', 'last_block_number')
    if not val:
      return 0

    last_block = val['last_block']
    return last_block

  def set_last_block(self):
    last_block_number = self.btc.get_block_count()

    # We need to satisfy a condition on looking only for blocks with at
    # least CONFIRMATIONS of confirmations
    satisfied = False

    while not satisfied:
      block_hash = self.btc.get_block_hash(last_block_number)
      block = self.btc.get_block(block_hash)
      if block['confirmations'] >= CONFIRMATIONS:
        satisfied = True
      else:
        last_block_number -= 1

    KeyValue(self.db).store('blocks', 'last_block_number', {'last_block':last_block_number})
    return last_block_number

  def get_new_block(self):
    last_block_number = self.get_last_block_number()

    if last_block_number == 0:
      last_block_number = self.set_last_block()

    newer_block = last_block_number + 1

    block_hash = self.btc.get_block_hash(newer_block)
    if not block_hash:
      return None

    block = self.btc.get_block(block_hash)

    # We are waiting for enough confirmations
    if block['confirmations'] < CONFIRMATIONS:
      return None

    logging.info("New block {}".format(newer_block))
    return block

  def handle_task(self, task):
    operation = task['operation']

    assert(operation in self.handlers)
    handler = self.handlers[operation]
    handler(self).handle_task(task)

    operation = task['operation']
    handler = self.handlers[operation]
    if handler:
      if handler(self).valid_task(task):
        return task
      else:
        logging.debug('Task marked as invalid by handler')
        self.task_queue.done(task)
        return None
    else:
      logging.debug("Task has invalid operation")
      self.task_queue.done(task)
      return None

  def is_fee_sufficient(self, addr, fee):
    if addr != self.oracle_address:
      return False
    if fee < Decimal(ORACLE_FEE):
      return False
    return True

  def prepare_request(self, request):
    try:
      fmsg = FastcastMessage(request)
    except:
      raise FastcastProtocolError()

    msg_body = json.loads(fmsg.message)

    if not 'operation' in msg_body:
      raise MissingOperationError()

    operation = msg_body['operation']
    return (operation, fmsg)

  def filter_requests(self, old_req):
    new_req = []

    last_received = self.kv.get_by_section_key('fastcast','last_epoch')['last']

    max_received = last_received

    for r in old_req:
      received_epoch = int(r['epoch'])
      if received_epoch > last_received:
        new_req.append(r)
        max_received = max(max_received, received_epoch)

    if len(new_req) > 0:
      self.kv.update('fastcast', 'last_epoch', {'last':max_received})

    return new_req

  def run(self):

    if not ORACLE_ADDRESS:
      self.oracle_address = self.kv.get_by_section_key('config','ORACLE_ADDRESS')

      if self.oracle_address is None:
        new_addr = self.btc.server.getnewaddress()
        self.oracle_address = new_addr
        logging.error("created a new address: '%s'" % new_addr)
        self.kv.store('config','ORACLE_ADDRESS',new_addr)
    else:
      self.oracle_address = ORACLE_ADDRESS

    logging.info("my multisig address is %s" % self.oracle_address)
    logging.info( "my pubkey: %r" % self.btc.validate_address(self.oracle_address)['pubkey'] )

    while True:
      # Proceed all requests
      requests = getMessages()
      requests = requests['results']

      requests = self.filter_requests(requests)

      for prev_request in requests:
        try:
          request = self.prepare_request(prev_request)
        except MissingOperationError:
          logging.info('message doesn\'t have operation field, invalid')
          logging.info(prev_request)
          continue
        except FastcastProtocolError:
          logging.info('message does not have all required fields')
          logging.info(prev_request)
          continue
        self.handle_request(request)


      task = self.task_queue.get_oldest_task()
      while task is not None:
        self.handle_task(task)
        self.task_queue.done(task)
        task = self.task_queue.get_oldest_task()

      new_block = self.get_new_block()

      if new_block:
        handlers = op_handlers.iteritems()

        addresses_per_handler = {}
        all_addresses = set()

        # Every handler can wait for transactions occuring on some addresses
        for name, handler in handlers:
          addresses = handler(self).get_observed_addresses()
          addresses_per_handler[name] = addresses
          for address in addresses:
            all_addresses.add(address)

        transactions = self.btc.get_transactions_from_block(new_block, list(all_addresses))

        handlers = op_handlers.iteritems()
        for name, handler in handlers:
          addresses = addresses_per_handler[name]
          handler_transactions = []
          for address in addresses:
            if address in transactions:
              handler_transactions.extend(transactions[address])
          handler(self).handle_new_transactions(handler_transactions)

        KeyValue(self.db).update('blocks', 'last_block_number', {'last_block':new_block['height']})

      time.sleep(10)
