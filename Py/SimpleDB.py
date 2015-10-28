from Date import Date
import shutil

class SimpleRecord:
  """
  A simple struct-like record.
  Allows setting (r[name] = value) and getting (r[value])
  As well as r.name = value and r.name (since the values are in __dict__)
  """
  def __init__( self, **fields ):
    self.__dict__.update( fields )

  def __getitem__( self, name ): # r[name]
    return self.__dict__[name]

  def __setitem__( self, name, value ): # r[name] = ...
    self.__dict__[name] = value

  def __nonzero__( self ): # for direct testing in if, while, assert
    return True

  def __str__( self ):
    res = []
    for k,v in self.__dict__.items():
      res.append( "%s:%s" % (str(k),str(v)) )
    return ", ".join(res)

  def __repr__( self ): return self.__str__()

  def __eq__( self, other ):
    d1 = self.__dict__
    d2 = other.__dict__
    if len(d1)!=len(d2): return False
    for k,v in d1.items():
      if k not in d2 or v != d2[k]: return False
    return True

  def check_fields( self, fld_names ):
    """Ensure that all fields from fld_names are present in the record
    Return first field that's not in self, otherwise ''
    """
    for f in fld_names:
      if f not in self.__dict__:
        return f
    return ''


def s_to_i( s ):
  """Helper fn - convert string to int"""
  try:
    return int(s)
  except:
    raise Exception( "invalid integer format: " + s )

def s_to_m( s ):
  """Helper fn - convert money (e.g. 'NNN.NN' or '$NNN.NN') to float"""
  try:
    if s.startswith('$'): return float( s[1:] )
    return float(s)
  except:
    raise Exception( "invalid money format: " + s )

def s_to_d( s ):
  """Helper fn - convert data string ('Y.M.D') to my Date value"""
  try:
    y,m,d = s.split('.')
    return Date(int(y),int(m),int(d))
  except:
    raise Exception( "invalid date format: " + s )

def escape( s ):
  """Helper fn - replace all <"> <'> <,> <%> to <%##>"""
  return s.replace("%","%25").replace(",","%2C").replace("'","%27").replace("\"","%22")

def unescape( s ):
  """Helper fn - replace all <%##> to corresp. chars (## is 00 to FF)"""
  res = ""
  pos = s.find( "%" )
  while pos >= 0:
    hex = s[pos+1:pos+3]
    res += s[:pos] + chr(int(hex,16))
    s = s[pos+3:]
    pos = s.find( "%" )
  return res + s


T_STR, T_INT, T_DATE, T_MONEY = 1,2,3,4 # enum Types
SDB_TYPES = { 'i':T_INT,'s':T_STR,'d':T_DATE,'m':T_MONEY } # s --> t

class ErrDB( Exception ):
  def __init__( self, fname, msg ):
    Exception.__init__( self, "File '%s': %s" % (fname, msg ) )


class SimpleDB:

  """
  SimpleDB( filename )
  --- first line is description "name:t","name:t",etc
  --- where t is type of the column:
  --- i - integer (INT)
  --- m - money   (MONEY)
  --- s - string  (STR)
  --- d - date    (DATE)
  --- first field is the key

  ._n_fields --> len(_field_names)
  ._field_names --> [ 'name1', 'name2', ... ]  # private
  ._field_types --> [ type1, type2, ... ]      # private
  ._records --> [ r1, r2, ... ] # each record - object with fields

  .field_names() --> [ 'name1', 'name2', ... ]
  .field_types() --> [ type1, type2, ... ]

  .add_record( r )      -- add internally
  .update_record( field_name, field_value, new_record ) -- update internally
  .find_record( field_name, field_value ) --> record | None
  .delete_record( field_name, field_value ) -- delete internally (return if found)
  .changed()            -- records were added/deleted after load/save
  .total_records()      -- number of records in db

  .get_records( fn_of_record=None ) --> [] | [idx] | [idx,...]
  .delete_records( field_name, field_value ) -- delete records

  .save() -- save updates to file
  """
  def __init__( self, fname ):

    self.file_name = fname # or path
    self._field_names = []
    self._field_types = []
    self._records = []
    self.descr_line = ''
    self.dirty  = False # changes made, needs saving
    self.backup = False # original file backed up

    try:
      f = file( fname, "rt" )
      self.descr_line = descr = f.readline().strip()
    except IOError:
      raise ErrDB( fname, "not found" )

    if not descr or len(descr)==0:
      raise ErrDB( fname, "invalid: no description" )

    def dequote( s ):
      """Get rid of outer quotes, "..." --> ... """
      # outer fname
      if s.startswith('"'):
        if s.endswith('"'): return s[1:-1] # get rid of ""
      elif not s.endswith('"'):
        return s
      raise ErrDB( fname, "mismatched quotes: " + s )

    # Read line 1 - description
    for d in descr.split(','):
      d = dequote( d.strip() )
      n,t = d.split(':')
      if not n.replace('_','').isalnum():
        raise ErrDB( fname, "invalid field name: " + n )
      if t not in SDB_TYPES:
        raise ErrDB( fname, "invalid field type: " + t )
      self._field_names.append( n )
      t = SDB_TYPES[t]
      self._field_types.append( t )
    self._n_fields = len(self._field_names)
    if self._n_fields==0:
      raise ErrDB( fname, "invalid description" )

    # Read the rest lines - records themselves
    line_cnt = 1
    for line in f.readlines():
      r = SimpleRecord()
      flds = line.strip().split(',')
      line_cnt += 1
      if len( flds ) != self._n_fields:
        raise ErrDB( fname, "wrong number of fields in line %d" % line_cnt )
      for i,s in enumerate( flds ):
        s = dequote( s.strip() )
        t = self._field_types[i]
        n = self._field_names[i]
        if   t == T_STR:    r[n] = unescape(s)
        elif t == T_INT:    r[n] = s_to_i(s)
        elif t == T_DATE:   r[n] = s_to_d(s) # DB format: yyyy.mm.dd
        elif t == T_MONEY:  r[n] = s_to_m(s)
        else: raise ErrDB( fname, "Internal error 1 in line %d: type " % line_cnt + t )
      self._records.append( r )
    self.dirty = False # just read, no changes yet

    f.close()
    # end __init__
    #print self.field_names
    #print self.field_types

  def field_names( self ): return self._field_names

  def field_types( self ): return self._field_types

  def total_records( self ): return len(self._records)

  def changed( self ):
    """True if records were added/deleted after open/save"""
    return self.dirty

  def add_record( self, record ): # record in python format (SimpleRecord)
    """Add a record to the base (internally), set flag dirty
    The argument is a record, fields are of python types: int, str, Date, float
    """
    self._records.append( record )
    self.dirty = True

  def find_record( self, name, value ):
    """Find record so that r.name == value and return it. Otherwise return None"""
    for r in self._records:
      if r[name]==value:
        return r
    return None

  def update_record( self, name, value, new_record ):
    """Find record so that r.name == value and update it."""
    for r in self._records:
      if r[name]==value:
        for n in self._field_names:
          if n in new_record.__dict__:
            r[n] = new_record[n]
            self.dirty = True
        return True
    return False

  def delete_record( self, name, value ):
    """Delete (first) record with r.name == value"""
    for i,r in enumerate(self._records):
      if r[name]==value:
        del self._records[i]
        self.dirty = True
        return True
    return False

  def delete_records( self, fn ):
    """Delete records such that fn(r) is True."""
    if fn is not None:
      nr = len(self._records)
      self._records = [r for r in self._records if not fn(r)]
      if len(self._records) != nr:
        self.dirty = True

  def get_records( self, fn=None ):
    """Find records such that fn(r) is True. Return list of records or []
    Without function return a copy of the list of all records"""
    if fn is None:
      return self._records[:]
    return [r for r in self._records if fn(r)]

  def save( self ):
    """Unconditionally put all data to the file, makes back-up if needed"""
    if not self.backup:
      try:
        ext = self.file_name.rfind( '.' )
        if ext < 0:
          bak_name = self.file_name + ".bak"
        else:
          bak_name = self.file_name[:ext] + ".bak"
        shutil.move( self.file_name, bak_name )
        self.backup = True
      except:
        raise Exception( "Can't make backup: " + bak_name )
    # Create file, write line 1 - description
    f = file( self.file_name, "wt" )
    print >>f, self.descr_line
    # Dump records
    for r in self._records:
      absent = r.check_fields( self._field_names )
      if absent:
        raise Exception( 'Field ' + absent + ' is not in the record')
      res = [] # join later with ','
      for n,t in zip( self._field_names, self._field_types ):
        v = r[n]
        if   t == T_STR:
          assert type(v)==str
          s = "\"%s\"" % escape(v) # replace commas, apostrophes, quotes, %
        elif t == T_INT:
          assert type(v)==int
          s = str(v)
        elif t == T_DATE:
          assert v.__class__ == Date
          s = str(v) # yyyy.mm.dd
        elif t == T_MONEY:
          assert type(v) in (int,float)
          s = "$%.2f" % v
        else:
          raise Exception( "Internal error 3: type " + t )
        res.append( s )
      print >>f, ','.join( res )
    # Done!
    f.close()
    self.dirty = False

# TEST

if __name__ == "__main__":
  n = "test1.sdb"

  f = file( n, "wt" )
  print >>f,"int_fld:i,date_fld:d,money_fld:m,string_fld:s"
  f.close()

  db = SimpleDB( n )
  assert db.total_records() == 0
  assert db.field_names() == ['int_fld','date_fld','money_fld','string_fld']
  assert db.field_types() == [T_INT,T_DATE,T_MONEY,T_STR]

  r1 = SimpleRecord()
  r1.int_fld = 11
  r1.date_fld = Date(2005,8,5)
  r1.money_fld = 1234.56
  r1.string_fld = "OK, 5% doesn't belong \"here\"!" # \n can't be in the string
  db.add_record(r1)

  r2 = SimpleRecord()
  r2['int_fld'] = 22
  assert r2['int_fld'] == r2.int_fld == 22
  r2['date_fld'] = Date(2005,3,19)
  r2['money_fld'] = 2345.67
  r2.string_fld = "This record will be deleted."
  assert r2.string_fld == r2['string_fld']
  db.add_record(r2)

  r3 = SimpleRecord( int_fld = 33, date_fld = Date(2005),
                     money_fld = 4567.89, string_fld = "" )
  db.add_record(r3)

  assert db.find_record( 'int_fld', 22 )
  assert db.find_record( 'money_fld', 1234.56 )
  assert not db.find_record( 'int_fld', 123 )

  res = db.delete_record( 'int_fld', 22 )
  assert res
  res = db.delete_record( 'int_fld', 22 )
  assert not res
  assert db.total_records()==2

  db.save()

  # re-read the data
  db = SimpleDB( n )
  assert db.total_records() == 2
  r2 = db.find_record( 'int_fld', 33 )
  assert r2.int_fld == r3.int_fld
  assert r2.date_fld == r3.date_fld
  assert r2.money_fld == r3.money_fld
  assert r2.string_fld == r3.string_fld
  assert r2 == r3
  db.save()

  f = file( n, "rt" )
  for l in f: print "::",l.strip()
  f.close()

  def add_records( db, recs ):
    for r in recs:
      db.add_record( SimpleRecord( int_fld = r[0], date_fld = r[1],
                            money_fld = r[2], string_fld = r[3] ) )

  # re-read the data
  db = SimpleDB( n )
  nr = db.total_records()
  add_records( db, [(34, Date(2005,5,5), 55.55, "Now" ),
                    (36, Date(2006,6,6), 66.66, "is" ),
                    (38, Date(2007,7,7), 77.77, "the" ),
                    (40, Date(2005,1,1), 11.55, "time" ),
                    (42, Date(2006,1,1), 11.66, "for" ),
                    (44, Date(2007,1,1), 11.77, "all" ),
                    (46, Date(2008,1,1), 11.88, "good" )] ) # +7

  db.delete_records( lambda r: r.date_fld.y==2008 ) # -1
  assert db.total_records() == nr + 6

  rr = db.get_records( lambda r: r.string_fld.startswith('t') )
  assert len(rr)==2

  # not saved to disk w/o save()

  import os
  os.remove( n )

# EOF
