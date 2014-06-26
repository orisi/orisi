from shared.db_classes import TableDb

class LockedPasswordTransaction(TableDb):
  """
  Database entry will keep locked password transaction, anyone can try to unlock it,
  finally it will be unlocked with time
  """
  table_name = 'locked_password_transaction'
  create_sql = 'create table {0} ( \
      id integer primary key autoincrement, \
      ts datetime default current_timestamp, \
      pwtxid text unique, \
      json_data text not null, \
      done integer default 0)'
  insert_sql = 'insert into {0} (pwtxid, json_data) values (?, ?)'
  all_sql = 'select * from {0} order by ts'
  pwtxid_sql = 'select * from {0} where pwtxid=?'
  mark_done_sql = 'update {0} set done=1 where pwtxid=?'

  def mark_as_done(self, pwtxid):
    cursor = self.db.get_cursor()
    sql = self.mark_done_sql.format(self.table_name)

    cursor.execute(sql, (pwtxid,))

  def args_for_obj(self, obj):
    return [obj['pwtxid'], obj['json_data']]

  def get_all(self):
    cursor = self.db.get_cursor()
    sql = self.all_sql.format(self.table_name)

    rows = cursor.execute(sql).fetchall()
    rows = [dict(row) for row in rows]
    return rows

  def get_by_pwtxid(self, pwtxid):
    cursor = self.db.get_cursor()
    sql = self.pwtxid_sql.format(self.table_name)

    row = cursor.execute(sql, (pwtxid, )).fetchone()
    if row:
      return dict(row)
    return None

class RSAKeyPairs(TableDb):
  table_name = 'rsa_keypairs'
  create_sql = 'create table {0} ( \
      id integer primary key autoincrement, \
      ts datetime default current_timestamp, \
      pwtxid text unique, \
      public text not null, \
      whole text not null)'
  insert_sql = 'insert into {0} (pwtxid, public, whole) values (?, ?, ?)'
  all_sql = 'select * from {0} order by ts'
  pwtxid_sql = 'select * from {0} where pwtxid=?'

  def args_for_obj(self, obj):
    return [obj['pwtxid'], obj['public'], obj['whole']]

  def get_all(self):
    cursor = self.db.get_cursor()
    sql = self.all_sql.format(self.table_name)

    rows = cursor.execute(sql).fetchall()
    rows = [dict(row) for row in rows]
    return rows

  def get_by_pwtxid(self, pwtxid):
    cursor = self.db.get_cursor()
    sql = self.pwtxid_sql.format(self.table_name)

    row = cursor.execute(sql, (pwtxid, )).fetchone()
    if row:
      return dict(row)
    return None


class RightGuess(TableDb):
  table_name = 'right_guess'
  create_sql = 'create table {0} ( \
      id integer primary key autoincrement, \
      ts datetime default current_timestamp, \
      pwtxid text not null, \
      guess text not null, \
      received_time integer not null)'
  insert_sql = 'insert into {0} (pwtxid, guess, received_time) values (?, ?, ?)'
  all_sql = 'select * from {0} order by ts'
  pwtxid_sql = 'select * from {0} where pwtxid=?'

  def args_for_obj(self, obj):
    return [obj['pwtxid'], obj['guess'], obj['received_time']]

  def get_all(self):
    cursor = self.db.get_cursor()
    sql = self.all_sql.format(self.table_name)

    rows = cursor.execute(sql).fetchall()
    rows = [dict(row) for row in rows]
    return rows

  def get_by_pwtxid(self, pwtxid):
    cursor = self.db.get_cursor()
    sql = self.pwtxid_sql.format(self.table_name)

    row = cursor.execute(sql, (pwtxid, )).fetchone()
    if row:
      return dict(row)
    return None

class SentPasswordTransaction(TableDb):
  table_name = 'sent'
  create_sql = 'create table {0} ( \
      id integer primary key autoincrement, \
      ts datetime default current_timestamp, \
      pwtxid text unique, \
      rqhs text not null, \
      tx text not null)'
  insert_sql = 'insert into {0} (pwtxid, rqhs, tx) values (?, ?, ?)'
  all_sql = 'select * from {0} order by ts'
  pwtxid_sql = 'select * from {0} where pwtxid=?'
  rqhs_sql = 'select * from {0} where rqhs=?'

  def args_for_obj(self, obj):
    return [obj['pwtxid'], obj['rqhs'], obj['tx']]

  def get_all(self):
    cursor = self.db.get_cursor()
    sql = self.all_sql.format(self.table_name)

    rows = cursor.execute(sql).fetchall()
    rows = [dict(row) for row in rows]
    return rows

  def get_by_pwtxid(self, pwtxid):
    cursor = self.db.get_cursor()
    sql = self.pwtxid_sql.format(self.table_name)

    row = cursor.execute(sql, (pwtxid, )).fetchone()
    if row:
      return dict(row)
    return None

  def get_by_rqhs(self, rqhs):
    cursor = self.db.get_cursor()
    sql = self.pwtxid_sql.format(self.table_name)

    row = cursor.execute(sql, (rqhs, )).fetchone()
    if row:
      return dict(row)
    return None
