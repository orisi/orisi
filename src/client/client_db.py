from shared.db_classes import GeneralDb, TableDb

CLIENT_DB_FILE = 'client.db'

class ClientDb(GeneralDb):
  def __init__(self):
    self._filename = CLIENT_DB_FILE
    self.connect()

class SignatureRequestDb(TableDb):
  """
  Used for saving transactions that were sent
  """
  table_name = 'sign_request'
  create_sql = 'create table {0} ( \
    id integer primary key autoincrement, \
    ts datetime default current_timestamp, \
    prevtx_hash text not null\
    json_data text not null);'
  insert_sql = 'insert into {0} (prevtx_hash, json_data) values (?, ?)'

  def args_for_obj(self, obj):
    return [obj['prevtx_hash'], obj['json_data']]

class MultisigRedeemDb(TableDb):
  """
  Save redeemScript for given multisig
  """
  table_name = 'multisig_redeem'
  create_sql = 'create table {0} ( \
    id integer primary key autoincrement, \
    ts datetime default current_timestamp, \
    multisig text not null, \
    redeem_script text not null, \
    min_sig integer not null, \
    pubkey_json text not null);'
  insert_sql = 'insert into {0} (multisig, redeem_script, min_sig, pubkey_json) values (?, ?, ?, ?)'

  def args_for_obj(self, obj):
    return [obj['multisig'], obj['redeem_script'], obj["min_sig"], obj['pubkey_json']]

class RawTransactionDb(TableDb):
  """
  Save raw transaction to retrieve some data from it later
  """
  table_name = 'raw_transaction'
  create_sql = 'create table {0} ( \
    id integer primary key autoincrement, \
    ts datetime default current_timestamp, \
    raw_transaction text not null, \
    txid text not null);'
  insert_sql = 'insert into {0} (raw_transaction, txid) values (?, ?)'

  def args_for_obj(self, obj):
    return [obj['raw_transaction'], obj['txid']]

class OracleListDb(TableDb):
  """
  Save current oracle list.
  """
  table_name = 'oracle_list'
  create_sql = 'create table {0} ( \
    id integer primary key autoincrement, \
    ts datetime default current_timestamp, \
    pubkey text not null, \
    address text not null, \
    fee text not null);'
  insert_sql = 'insert into {0} (pubkey, address, fee) values (?, ?, ?)'

  def args_for_obj(self, obj):
    return [obj['pubkey'], obj['address'], obj['fee']]
