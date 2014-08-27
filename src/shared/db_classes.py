import sqlite3

class GeneralDb:

  def __init__(self, filename):
    self._filename = filename
    self.connect()

  def connect(self):
    self.conn = sqlite3.connect(self._filename, detect_types=sqlite3.PARSE_COLNAMES)
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


class TableDb(object):
  """
  TableDb is class designed as wrapper for new tables and database requests.
  It creates table when needed, so no need to worry about it
  """
  table_name = "TableDB"
  exist_sql = "select name from sqlite_master where type='table' and name='{0}'"

  def __init__(self, db):
    self.db = db
    if not self.table_exists():
      self.create_table()

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

  def args_for_obj(self, obj):
    raise NotImplementedError()

  def args_for_obj_update(self, obj):
    raise NotImplementedError()

  def args_for_obj_delete(self, obj):
    raise NotImplementedError()

  def insert_with_sql(self, sql, args):
    cursor = self.db.get_cursor()
    cursor.execute(sql, args)
    self.db.commit()

  def execute_sql_properly(self, sql, args):
    cursor = self.db.get_cursor()
    cursor.execute(sql, args)
    self.db.commit()

  def save(self, obj):
    sql = self.insert_sql.format(self.table_name)
    args = self.args_for_obj(obj)
    self.execute_sql_properly(sql, args)

  def update(self, obj):
    sql = self.update_sql.format(self.table_name)
    args = self.args_for_obj_update(obj)
    self.execute_sql_properly(sql, args)

  def delete(self, obj):
    sql = self.delete_sql.format(self.table_name)
    args = self.args_for_obj_delete(obj)
    self.execute_sql_properly(sql, args)
