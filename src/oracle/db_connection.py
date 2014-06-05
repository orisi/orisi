from collections import defaultdict

import sqlite3
import time

ORACLE_FILE = 'oracle.db'

class OracleDb:

  def __init__(self):
    self.connect()
    operations = {
      'TransactionRequest': TransactionRequestDb
    }
    self.operations = defaultdict(lambda: False, operations)

  def connect(self):
    self.conn = sqlite3.connect(ORACLE_FILE)
    self.conn.row_factory = sqlite3.Row

  def commit(self):
    self.conn.commit()

  def execute(self, sql):
    cursor = self.conn.cursor()
    cursor.execute(sql)
    self.conn.commit()

  def get_cursor(self):
    if not self.conn:
      self.connect()

    try:
      return self.conn.cursor()
    except:
      self.connect()
      return self.conn.cursor()


class TableDb:
  """
  TableDb is class designed as wrapper for new tables and database requests.
  It creates table when needed, so no need to worry about it
  """
  table_name = "TableDB"
  exist_sql = "select name from sqlite_master where type='table' and name='{0}'"

  def __init__(self, db):
    self.db = db
  
  def table_exists(self):
    cursor = self.db.get_cursor()
    sql = self.exist_sql.format(self.table_name)
    cursor = cursor.execute(sql)
    results = cursor.fetchall()
    return len(results) > 0

  def create_table(self):
    cursor = self.db.get_cursor()
    sql = self.create_sql.format(self.table_name)
    cursor.execute(sql)
    self.db.commit()

  def insert_object(self, obj):
    sql = self.insert_sql.format(self.table_name)
    args = self.args_for_obj(obj)
    self.insert_with_sql(sql, args)

  def args_for_obj(self, obj):
    raise NotImplementedError()

  def insert_with_sql(self, sql, args):
    cursor = self.db.get_cursor()
    cursor.execute(sql, args)
    self.db.commit()

  def save(self, obj):
    if not self.table_exists():
      self.create_table()

    self.insert_object(obj)

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
      json_data text not null, \
      origin_address text not null, \
      next_check integer not null, \
      done integer default 0);"
  insert_sql = "insert into {0} (origin_address, json_data, next_check, done) values (?,?,?)"
  oldest_sql = "select * from {0} where next_check<? order by ts limit 1"

  def args_for_obj(self, obj):
    return [obj["origin_address"], obj["json_data"], obj["next_check"], obj["done"]]

  def get_oldest_task(self):
    cursor = self.db.get_cursor()
    sql = self.oldest_sql.format(self.table_name)

    row = cursor.execute(sql, int(time.time())).fetchone()
    result = dict(row)
    return result










