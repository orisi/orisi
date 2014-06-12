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
    prevtx_hash text not null, \
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
  get_address_sql = 'select * from {0} where multisig=? order by ts desc limit 1'

  def args_for_obj(self, obj):
    return [obj['multisig'], obj['redeem_script'], obj["min_sig"], obj['pubkey_json']]

  def get_address(self, address):
    cursor = self.db.get_cursor()
    sql = self.get_address_sql.format(self.table_name)

    row = cursor.execute(sql, [address,]).fetchone()
    if row:
      return dict(row)
    return row

class RawTransactionDb(TableDb):
  """
  Save raw transaction to retrieve some data from it later
  """
  table_name = 'raw_transaction'
  create_sql = 'create table {0} ( \
    id integer primary key autoincrement, \
    ts datetime default current_timestamp, \
    raw_transaction text not null, \
    txid text unique);'
  insert_sql = 'insert or ignore into {0} (raw_transaction, txid) values (?, ?)'
  get_tx_sql = 'select * from {0} where txid=? limit 1'

  def args_for_obj(self, obj):
    return [obj['raw_transaction'], obj['txid']]

  def get_tx(self, txid):
    cursor = self.db.get_cursor()
    sql = self.get_tx_sql.format(self.table_name)

    row = cursor.execute(sql, [txid,]).fetchone()
    if row:
      return dict(row)
    return row

class OracleListDb(TableDb):
  """
  Save current oracle list.
  """
  table_name = 'oracle_list'
  create_sql = 'create table {0} ( \
    id integer primary key autoincrement, \
    ts datetime default current_timestamp, \
    pubkey text not null, \
    address text unique, \
    fee text not null);'
  insert_sql = 'insert or replace into {0} (pubkey, address, fee) values (?,?,?)'
  get_oracles_sql = 'select * from {0} where address in ({1})'
  get_all_oracles_sql = 'select * from {0}'

  def args_for_obj(self, obj):
    return [obj['pubkey'], obj['address'], obj['fee']]

  def get_oracles(self, oracle_addresses):
    cursor = self.db.get_cursor()
    sql = self.get_oracles_sql.format(self.table_name, ','.join('?'*len(oracle_addresses)))

    rows = cursor.execute(sql, oracle_addresses).fetchall()
    rows = [dict(row) for row in rows]
    return rows

  def get_all_oracles(self):
    cursor = self.db.get_cursor()
    sql = self.get_all_oracles_sql.format(self.table_name)
    rows = cursor.execute(sql).fetchall()
    rows = [dict(row)for row in rows]
    return rows

class OracleCheckDb(TableDb):
  """
  Keeps check times of remote oracle list.
  """
  table_name = 'oracle_checktime'
  create_sql = 'create table {0} ( \
    id integer primary key autoincrement, \
    ts datetime default current_timestamp, \
    last_check integer not null);'
  insert_sql = 'insert into {0} (last_check) values (?)'
  oldest_sql = "select * from {0} order by last_check desc limit 1"

  def args_for_obj(self, obj):
    return [obj["last_check"], ]

  def get_last(self):
    cursor = self.db.get_cursor()
    sql = self.oldest_sql.format(self.table_name)

    row = cursor.execute(sql).fetchone()
    if row:
      row = dict(row)
    return row









