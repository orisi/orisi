from collections import defaultdict
from shared.db_classes import TableDb, GeneralDb

import json
import time

ORACLE_FILE = 'oracle.db'

class KeyValue(TableDb):
  table_name = 'key_value'
  create_sql = 'create table {0} ( \
      id integer primary key autoincrement, \
      section varchar(255) not null, \
      keyid varchar(255) not null, \
      value text not null )'
  insert_sql = 'insert into {0} (section, keyid, value) values (?, ?, ?)'
  update_sql = 'update {0} set value=? where section=? and keyid=?'
  all_sql = 'select * from {0} order by id'
  get_sql = 'select * from {0} where section=? and keyid=? order by id desc'

  def args_for_obj_save(self, obj):
    return [obj['section'], obj['keyid'], json.dumps(obj['value'])]

  def args_for_obj_update(self, obj):
    return [obj['value'], obj['section'], obj['keyid']]

  def store ( self, section, keyid, value ):
    assert( self.get_by_section_key(section, keyid) is None )
    return self.save({ 'section': section, 'keyid': keyid, 'value': value })

  def update ( self, section, keyid, value ):
    #tbd: replace this with an actual "update" sql
    return self.save({ 'section': section, 'keyid': keyid, 'value': value })


  def get_by_section_key(self, section, keyid):
    cursor = self.db.get_cursor()
    sql = self.get_sql.format(self.table_name)

    row = cursor.execute(sql, (section, keyid, )).fetchone()
    if row:
      d = dict(row)
      d['value'] = json.loads(d['value'])
      return d['value']
    return None


class OracleDb(GeneralDb):

  def __init__(self):
    self._filename = ORACLE_FILE
    self.connect()
    operations = {
      'conditioned_transaction': TransactionRequestDb
    }
    self.operations = defaultdict(lambda: False, operations)


# XRequestDb - are classes for saving requests in history

class TransactionRequestDb(TableDb):
  """
  Used for saving transaction requests to DB (only requests,)
  """
  table_name = "transaction_requests"
  create_sql = "create table {0} ( \
    id integer primary key autoincrement, \
    ts datetime default current_timestamp, \
    from_address text not null, \
    json_data text not null);"
  insert_sql = "insert into {0} (from_address, json_data) values (?, ?)"

  def args_for_obj(self, obj):
    return [obj.from_address, obj.message]

class TaskQueue(TableDb):
  """
  Class responsible for saving transactions we're going to sign later.
  It accepts JSON, so we can add basically any task we'd like and parse
  it later.
  """

  table_name = "task_queue"

  create_sql = "create table {0} ( \
      id integer primary key autoincrement, \
      ts datetime default current_timestamp, \
      operation text not null, \
      json_data text not null, \
      next_check integer not null, \
      done integer default 0);"
  insert_sql = "insert into {0} (operation, json_data, next_check, done) values (?,?,?,?)"
  oldest_sql = "select * from {0} where next_check<? and done=0 order by ts limit 1"
  all_sql = "select * from {0} where next_check<? and done=0 order by ts"
  all_ignore_sql = "select * from {0} where done=0 order by ts"
  mark_done_sql = "update {0} set done=1 where id=?"

  def args_for_obj(self, obj):
    return [obj['operation'], obj['json_data'], obj['next_check'], obj['done']]

  def get_oldest_task(self):
    cursor = self.db.get_cursor()
    sql = self.oldest_sql.format(self.table_name)

    row = cursor.execute(sql, (int(time.time()), )).fetchone()
    if row:
      row = dict(row)
    return row

  def get_all_tasks(self):
    cursor = self.db.get_cursor()
    sql = self.all_sql.format(self.table_name)

    rows = cursor.execute(sql, (int(time.time()), )).fetchall()
    rows = [dict(row) for row in rows]
    return rows

  def get_all_ignore_checks(self):
    cursor = self.db.get_cursor()
    sql = self.all_ignore_sql.format(self.table_name)

    rows = cursor.execute(sql).fetchall()
    rows = [dict(row) for row in rows]
    return rows

  def done(self, task):
    cursor = self.db.get_cursor()
    sql = self.mark_done_sql.format(self.table_name)
    cursor.execute(sql, (int(task['id']), ))

class UsedInput(TableDb):
  """
  Class that adds what transaction we want to sign. When new transaction comes through with
  same address, but different inputs and outputs we won't sign it!
  """
  table_name = "used_input"
  create_sql = "create table {0} ( \
      id integer primary key autoincrement, \
      ts datetime default current_timestamp, \
      input_hash text unique);"
  insert_sql = "insert or ignore into {0} (input_hash) values (?)"
  exists_sql = "select * from {0} where input_hash=?"

  def args_for_obj(self, obj):
    return [obj["input_hash"]]

  def get_input(self, i):
    sql = self.exists_sql.format(self.table_name)
    cursor = self.db.get_cursor()
    row = cursor.execute(sql, (i, ) ).fetchone()
    if row:
      result = dict(row)
      return result
    else:
      return None


class SignedTransaction(TableDb):
  """
  Class that will keep all transactions signed by oracle (possible multiplications for now)
  """
  table_name = "signed_transaction"
  create_sql = "create table {0} ( \
      id integer primary key autoincrement, \
      ts datetime default current_timestamp, \
      hex_transaction text not null, \
      prevtx text not null)"
  insert_sql = "insert into {0} (hex_transaction, prevtx) values (?, ?)"
  all_sql = "select * from {0} order by ts"

  def args_for_obj(self, obj):
    return [obj["hex_transaction"], obj["prevtx"]]

  def get_all(self):
    cursor = self.db.get_cursor()
    sql = self.all_sql.format(self.table_name)

    rows = cursor.execute(sql).fetchall()
    rows = [dict(row) for row in rows]
    return rows


class HandledTransaction(TableDb):
  """
  Class that will take care of keeping information which txid were already handled
  and how many signatures they got
  """
  table_name = "handled_tx"
  create_sql = "create table {0} ( \
      id integer primary key autoincrement, \
      ts datetime default current_timestamp, \
      rqhs text unique, \
      max_sigs integer not null);"
  insert_sql = "insert or replace into {0} (rqhs, max_sigs) values (?,?)"
  tx_sql = "select max_sigs from {0} where rqhs=?"

  def args_for_obj(self, obj):
    return [obj['rqhs'], obj['max_sigs']]

  def signs_for_transaction(self, rqhs):
    cursor = self.db.get_cursor()
    sql = self.tx_sql.format(self.table_name)

    row = cursor.execute(sql, (rqhs, )).fetchone()
    if row:
      row = dict(row)
      return row['max_sigs']
    else:
      sql = self.insert_sql.format(self.table_name)
      cursor.execute(sql, (rqhs, 0))
    return 0

  def update_tx(self, rqhs, sigs):
    self.save({"rqhs":rqhs, "max_sigs":sigs})




