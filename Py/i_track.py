#!/usr/bin/env python

NAME_VERS = 'Invoice Tracker 1.107' # 2012-03-02 00:31:51 * $@{2vYmdHMS}

# Make the distribution package with "setup.py py2exe"

from Date import Date
from SimpleDB import SimpleDB, SimpleRecord, ErrDB, T_STR,T_INT,T_DATE,T_MONEY
from RecordDlg import RecordDlg

import time # for CustomStatusBar.Notify
import os, os.path
import wx
from wx.lib.printout import PrintTable
#from CalendarDlg import CalendarDlg

CURRENT_DATE = Date() # today
CURRENT_YEAR = CURRENT_DATE.y
ST_OVERDUE = "overdue"
ST_PENDING = "pending"

def MsgBox( window, msg, t='Info' ):
  dlg=wx.MessageDialog( window, msg, t, wx.OK ) # | wxICON_INFORMATION
  dlg.ShowModal()
  dlg.Destroy()

class CustomStatusBar( wx.StatusBar ):
  def __init__( self, parent, fname ):
    wx.StatusBar.__init__( self, parent, -1 )

    # This status bar has three fields
    self.SetFieldsCount(3)
    # Sets the three fields to be relative widths to each other.
    self.SetStatusWidths( [-2, -1, -2] )
    self.sizeChanged = False
    self.Bind( wx.EVT_SIZE, self.OnSize )
    self.Bind( wx.EVT_IDLE, self.OnIdle )

    # Field 0 ... just text
    self.SetStatusText( fname, 0 )

    # This will fall into field 1 (the second field)
    self.cb = wx.CheckBox(self, 1001, "Clock")
    self.Bind( wx.EVT_CHECKBOX, self.OnToggleClock, self.cb )
    self.cb.SetValue(True)

    # set the initial position of the checkbox
    self.Reposition()

    # We're going to use a timer to drive a 'clock' in the last field.
    self.timer = wx.PyTimer( self.Notify )
    self.timer.Start(1000)
    self.Notify()

  # Handles events from the timer we started in __init__().
  # We're using it to drive a 'clock' in field 2 (the third field).
  def Notify(self):
    t = time.localtime( time.time() )
    st = time.strftime( "%d-%b-%Y  %H:%M:%S", t )
    self.SetStatusText( st, 2 )

  # the checkbox was clicked
  def OnToggleClock(self, event):
    if self.cb.GetValue():
      self.timer.Start(1000)
      self.Notify()
    else:
      self.timer.Stop()

  def OnSize(self, evt):
    self.Reposition()  # for normal size events

    # Set a flag so the idle time handler will also do the repositioning.
    # It is done this way to get around a buglet where GetFieldRect is not
    # accurate during the EVT_SIZE resulting from a frame maximize.
    self.sizeChanged = True

  def OnIdle(self, evt):
    if self.sizeChanged:
      self.Reposition()

  # reposition the checkbox
  def Reposition(self):
    rect = self.GetFieldRect(1)
    self.cb.SetPosition( (rect.x+2, rect.y+2) )
    self.cb.SetSize( (rect.width-4, rect.height-4) )
    self.sizeChanged = False


# Commands
# NEW OPEN
ADD     = wx.NewId()
EDIT    = wx.NewId()
INFO    = wx.NewId()
CLOSE   = wx.NewId()
DISPLAY = wx.NewId()
DELETE  = wx.NewId()
PRINT   = wx.NewId()
SAVE    = wx.NewId()
LOAD    = wx.NewId()
FILTER  = wx.NewId()
ABOUT   = wx.NewId()

Parent = wx.Frame # can be wx.Dialog but with some different behaviour

class WorkFrame( Parent ):

  def _read_db( self, db_path ):
    self.db_path = db_path
    self.db_name = os.path.basename( db_path )
    self.db = SimpleDB( self.db_path )
    self.names = self.db.field_names()
    self.types = self.db.field_types()
    self.NF = len(self.names)
    self.key = self.names[0]

  def _load_db( self, db_path ):
    self._read_db( db_path ) # sets db and other stuff

    self.status_bar = CustomStatusBar( self, self.db_name )
    self.SetStatusBar( self.status_bar )

    self.companies = {} # a set

    self.sorted = (0,True) # None or (col_idx,ascending) col_idx=0|1|... asc:bool
    self.mark_col( 0, True )

    self.c_date = Date(2000,1,1) # last checked date (far past), for check_overdue
    self.check_overdue( dont_refresh=True )

    self.curr = 0 # current record, index in the list ListCtrl
    self.refresh() # filter and sort are inside
    self.lc.SetItemState(self.curr, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

  def __init__( self, parent, id, title, filepath, **kwds ):

    self.title = title
    self.parent = parent

    Parent.__init__( self, parent, id, title, **kwds )

    # .lc - the main table
    # it keeps record no in its user-data field
    self.lc = wx.ListCtrl( self, DISPLAY,
        style=wx.LC_REPORT|wx.LC_SINGLE_SEL, size=(700,450) )

    self.column_names = ['Inv.','Date Done','Customer','Description',
                          'Amount','Date Due','Status']
    for i,h in enumerate(self.column_names):
      self.lc.InsertColumn(i,h)

    self.butsave   = wx.Button(self, SAVE,   "Save")
    self.butprint  = wx.Button(self, PRINT,  "Print")
    self.butinfo   = wx.Button(self, INFO,   "Info")
    self.butadd    = wx.Button(self, ADD,    "Add")
    self.butedit   = wx.Button(self, EDIT,   "Edit")
    self.butdelete = wx.Button(self, DELETE, "Delete")
    self.butload   = wx.Button(self, LOAD,   "Load")
    self.butfilter = wx.Button(self, FILTER, "Filter")
    self.butabout  = wx.Button(self, ABOUT,  "About")
    self.butclose  = wx.Button(self, CLOSE,  "Quit")

    self._do_layout()

    wx.EVT_BUTTON( self, SAVE, self.on_save )
    wx.EVT_BUTTON( self, PRINT, self.on_print )
    wx.EVT_BUTTON( self, INFO, self.on_info )
    wx.EVT_BUTTON( self, ADD, self.on_add )
    wx.EVT_BUTTON( self, EDIT, self.on_edit )
    wx.EVT_BUTTON( self, DELETE, self.on_delete )
    wx.EVT_BUTTON( self, FILTER, self.on_filter )
    wx.EVT_BUTTON( self, LOAD, self.on_load )
    wx.EVT_BUTTON( self, CLOSE, self.on_close )
    wx.EVT_BUTTON( self, ABOUT, self.on_about )
    wx.EVT_LIST_ITEM_SELECTED( self, DISPLAY, self.display )
    self.lc.Bind( wx.EVT_LEFT_DCLICK, self.on_double_click )
    self.lc.Bind( wx.EVT_RIGHT_DOWN, self.on_right_down )
    # for wxMSW
    self.lc.Bind( wx.EVT_COMMAND_RIGHT_CLICK, self.on_right_click )
    # for wxGTK
    self.lc.Bind( wx.EVT_RIGHT_UP, self.on_right_click )
    self.Bind( wx.EVT_LIST_COL_CLICK, self.on_col_click, self.lc )
    self.Bind( wx.EVT_CLOSE, self.on_close )

    def default_filter(r):
      return r.date_due.y==CURRENT_YEAR or r.status in (ST_OVERDUE,ST_PENDING)
    def no_filter(r): return True
    def filter_pending(r): return r.status==ST_PENDING
    def filter_overdue(r): return r.status==ST_OVERDUE
    def filter_2003(r): return r.date_due.y==2003
    def filter_2004(r): return r.date_due.y==2004
    def filter_2005(r): return r.date_due.y==2005
    def filter_2006(r): return r.date_due.y==2006
    def filter_2007(r): return r.date_due.y==2007
    def filter_2008(r): return r.date_due.y==2008
    def filter_2009(r): return r.date_due.y==2009
    def filter_2010(r): return r.date_due.y==2010
    def filter_2011(r): return r.date_due.y==2011
    def filter_2012(r): return r.date_due.y==2012
    def filter_2013(r): return r.date_due.y==2013
    def filter_2014(r): return r.date_due.y==2014
    def filter_2015(r): return r.date_due.y==2015
    def filter_2016(r): return r.date_due.y==2016
    def filter_2017(r): return r.date_due.y==2017
    def filter_2018(r): return r.date_due.y==2018
    def filter_2019(r): return r.date_due.y==2019

    self.filters = [default_filter,no_filter,filter_pending,filter_overdue,
      filter_2003,filter_2004,filter_2005,filter_2006,filter_2007,filter_2008,filter_2009,filter_2010,
      filter_2011,filter_2012,filter_2013,filter_2014,filter_2015,filter_2016,filter_2017,filter_2018,
      filter_2019]
    self.filter_descrs = ["Default: this year and all pending/overdue",
      "All invoices ==============================",
      "All pending","All overdue",
      "2003","2004","2005","2006","2007","2008","2009","2010","2011","2012","2013","2014","2015",
      "2016","2017","2018","2019"]

    self.filter_no = 0
    self.filter_fn = self.filters[self.filter_no] # for refresh()

    self._load_db( filepath )

    self.timer = wx.PyTimer( self.check_overdue )
    self.timer.Start(30000) # every 30 seconds

  def _do_layout(self):
    boxa = wx.BoxSizer(wx.VERTICAL)
    boxt = wx.BoxSizer(wx.VERTICAL)
    boxb = wx.BoxSizer(wx.HORIZONTAL)
    CVH = wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL
    boxt.Add( self.lc, 1, wx.EXPAND )
    boxb.Add( self.butsave, 0, CVH )
    boxb.Add( self.butprint, 0, CVH )
    boxb.Add( self.butinfo, 0, CVH )
    boxb.Add( self.butadd, 0, CVH )
    boxb.Add( self.butedit, 0, CVH )
    boxb.Add( self.butdelete, 0, CVH )
    boxb.Add( self.butfilter, 0, CVH )
    boxb.Add( self.butload, 0, CVH )
    boxb.Add( self.butabout, 0, CVH )
    boxb.Add( self.butclose, 0, CVH )
    boxa.Add( boxt,1, wx.EXPAND )
    boxa.Add( boxb,0, wx.EXPAND )
    self.SetAutoLayout(1)
    self.SetSizer(boxa)
    boxa.Fit(self)
    boxa.SetSizeHints(self)
    self.Layout()

  # Mark-unmark columns when sorting

  def unmark_col( self, n ):
    """Remove 'sorting' mark from the column title.
    The fn asumes the title ends with ' [+] ' or ' [--]'
    """
    c = self.lc.GetColumn( n )
    c.SetText( c.GetText()[:-5] )
    c.m_mask = wx.LIST_MASK_TEXT
    self.lc.SetColumn( n, c )

  def refresh_status_line( self ):
    st = "File: %s%s - %d/%d records" % (self.db_name,
      (self.db.dirty and " *" or ""),
      self.n_records, self.total_records)
    self.status_bar.SetStatusText( st, 0 )

  def refresh( self ):
    """Re-read the database table,
    Apply filter,
    Sort,
    Re-build the lc"""
    self.lc.DeleteAllItems()
    self.records = self.db.get_records( self.filter_fn ) # Filter
    self.sort_records()
    for i,r in enumerate(self.records):
      self.lc.InsertStringItem(i,self.fmt_field(r,0))
      for j in range(1,self.NF):
        self.lc.SetStringItem(i,j,self.fmt_field(r,j))
      self.lc.SetItemData(i,i)
      if r.status == ST_OVERDUE:
        self.lc.SetItemTextColour(i, (255,0,0) ) # red
      elif r.status == ST_PENDING:
        self.lc.SetItemTextColour(i, (0,0,255) ) # blue
      self.companies[ r.customer ] = True
    self.n_records = len(self.records)
    self.total_records = self.db.total_records()
    self.refresh_status_line()

  def find_record_index( self, key ):
    for i,r in enumerate(self.records):
      if r[self.key]==key:
        return i
    return -1

  def mark_col( self, n, ord ):
    """Adds 'sorting' mark to column n (ord ? ' [+] ' ! ' [--]')
    n:int - column number, ord:bool - ascending
    """
    c = self.lc.GetColumn( n )
    t = c.GetText()
    t += ord and " [+] " or " [--]"
    c.SetText( t )
    c.m_mask = wx.LIST_MASK_TEXT
    self.lc.SetColumn( n, c )

  # Click on column title - sort

  def sort_records( self ):
    if not self.sorted:
      return
    (n, o) = self.sorted
    m = self.names[n]
    s = self.records
    if o:
      def fsrt(a,b): return cmp( a[m], b[m] ) # asc
    else:
      def fsrt(a,b): return cmp( b[m], a[m] ) # dsc
    #self.lc.SortItems( fsrt )
    s.sort( cmp=fsrt )

  def do_sort( self ):
    r = self.curr>=0 and self.records[ self.curr ] or None
    self.sort_records()
    self.refresh()
    if r:
      self._goto_rec( r )

  def on_col_click( self, event ):
    """click on a column title - sort"""
    n = event.GetColumn()
    event.Skip()
    # mark/unmark columns
    o = True # order to be
    if self.sorted:
      on,oo = self.sorted
      if on == n: o = not oo
      self.unmark_col( on )
    self.mark_col( n, o )
    self.sorted = ( n, o )
    self.do_sort()
    # the current selection is preserved

  # Current item

  def display( self, event ):
    curitem = event.m_itemIndex
    self.curr = self.lc.GetItemData( curitem )

  # Double click - edit

  def on_double_click( self, event ):
    self.on_edit( event )

  # Right button - pop-up menu

  def on_right_down( self, event ):
    self.x = event.GetX()
    self.y = event.GetY()
    item, flags = self.lc.HitTest( (self.x, self.y) )
    if flags & wx.LIST_HITTEST_ONITEM:
      self.lc.Select(item)
      self.inside = True
    else:
      self.inside = False
    event.Skip()

  def on_right_click( self, event ):
    if not self.inside:
      return
    # only do this part the first time so the events are only bound once
    if not hasattr( self, "popupID1" ):
      self.popupID1 = wx.NewId() # Edit
      self.popupID2 = wx.NewId() # Delete
      self.popupID3 = wx.NewId() # Mark as Paid

      self.Bind( wx.EVT_MENU, self.on_popup_one, id=self.popupID1 )
      self.Bind( wx.EVT_MENU, self.on_popup_two, id=self.popupID2 )
      self.Bind( wx.EVT_MENU, self.on_popup_three, id=self.popupID3 )

    # make a menu
    menu = wx.Menu()
    # add some items
    menu.Append( self.popupID1, "Edit"   )
    menu.Append( self.popupID2, "Delete" )
    menu.Append( self.popupID3, "Paid!"  )

    # Popup the menu.  If an item is selected then its handler
    # will be called before PopupMenu returns.
    self.PopupMenu( menu, (self.x, self.y) )
    menu.Destroy()

  def on_popup_one( self, event ): # Edit
    self.on_edit( event )

  def on_popup_two( self, event ): # Delete
    self.on_delete( event )

  def on_popup_three( self, event ): # Clean status
    r = self.records[ self.curr ]
    r.status = ''
    self.db.dirty = True
    self.refresh()
    self._goto_rec( r )

  def fmt_field( self, r, i ):
    v = r[self.names[i]]
    t = self.types[i]
    if   t == T_STR:   return v
    elif t == T_INT:   return str(v)
    elif t == T_DATE:  return v.format( "%a" )
    elif t == T_MONEY: return "$%.2f" % v

  def check_overdue( self, dont_refresh=False ):
    """Runs thru all the records in DB and changes 'pending' to 'overdue'
    is the current date/time > r.date_due"""
    d = Date() # today
    if d == self.c_date: # check only once a day
      return
    self.c_date = d
    c = 0  # changed records
    recs = self.db.get_records() # for all records
    for r in recs:
      if r.status == ST_PENDING and d > r.date_due:
        r.status = ST_OVERDUE
        c += 1
    if c > 0:
      # MsgBox( self, "%d records changed 'pending' to 'overdue'." % c )
      self.db.dirty = True
      if not dont_refresh:
        self.refresh()

  def _add_rec( self, rec ):
    self.db.add_record( rec )
    self.refresh()

  def _goto_rec( self, rec ):
    i = self.find_record_index( rec[self.key] )
    if i<0: i=self.n_records-1
    self.curr = i
    self.lc.SetItemState(self.curr, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

  def on_add( self, event ):
    maxinv = 0
    for r in self.records:
      inv = r[self.key] # r.invoice
      if inv > maxinv:
        maxinv = inv
    dlg = RecordDlg( self, "Add New Entry", None, maxinv+1 )
    val = dlg.ShowModal()
    if val and dlg.rec:
      self._add_rec( dlg.rec )
      self._goto_rec( dlg.rec )
    dlg.Destroy()

  def on_edit( self, event ):
    if self.curr < 0:
      MsgBox( self, "No record selected" )
      return
    r = self.records[self.curr]
    k = r[self.key] # key value
    dlg = RecordDlg( self, "Edit Entry", r, None )
    val = dlg.ShowModal()
    rec = dlg.rec # can be None
    dlg.Destroy()
    if val and rec:
      self.db.update_record( self.key, k, rec )
      self.refresh()
      self._goto_rec( r )

  def on_delete( self, event ):
    if self.curr < 0:
      MsgBox( self, "No record selected" )
      return
    r = self.records[self.curr]
    x = r.invoice, r.customer, r.descr
    mg = ("Are You Sure You want to delete record\n"+
          "    Invoice:  \t%d\n    Customer:\t%s\n    Descriptn:\t%s") % x
    msg = wx.MessageDialog( self, mg, "Deleting", wx.OK|wx.CANCEL )
    res = msg.ShowModal()
    msg.Destroy()
    if res == wx.ID_OK:
      self.db.delete_record( self.key, r[self.key] )
      self.refresh()
      if self.curr >= self.n_records:
        self.curr = self.n_records - 1 # last record or -1 if no records
      if self.curr >= 0:
        self.lc.SetItemState(self.curr, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)

  def on_print( self, event ):
    data = []
    for i,r in enumerate(self.records):
      line = []
      for j in range(self.NF):
        line.append( self.fmt_field(r,j) )
      data.append( line )
    prt = PrintTable(self.parent)
    prt.data = data
    prt.left_margin = 0.5
    #prt.top_margin = 1
    prt.set_column = [0.8, 1.0, 3.0, 2.5, 1.0, 1.0, 0.8]
    prt.label = ["Invoice","Date Done","Customer","Description","Amount", "Date Due", "Status"]
    prt.SetColAlignment(4, wx.ALIGN_RIGHT)
    prt.SetLandscape()
    prt.SetHeader( "Invoice List Report", size = 30 )
    prt.SetFooter("Date: ", type = "Date", align=wx.ALIGN_RIGHT, indent = -2, colour = wx.NamedColour('BLUE'))
    #prt.SetRowSpacing( 10,10 )
    prt.Preview() # Print()

    red = wx.NamedColour('RED')
    blue = wx.NamedColour('BLUE')
    for i,r in enumerate(data):
      if r[6] == ST_OVERDUE:
        for j in range(self.NF):
          prt.SetCellText( i,j, red )
          prt.SetCellColour( i,j, (255,200,200))
      elif r[6] == ST_PENDING:
        for j in range(self.NF):
          prt.SetCellText( i, j, blue )
          prt.SetCellColour( i,j, (200,200,255))

    return

  def on_save( self, event ):
    self.db.save()
    self.refresh_status_line()

  def on_load( self, event ):
    dlg = wx.FileDialog( self, message="Choose a file",
      defaultDir=os.getcwd(), # starting dir = current dir
      defaultFile="",
      wildcard="Invoice Track database (*.tdb)|*.tdb|All files (*.*)|*.*",
      style=wx.OPEN | wx.CHANGE_DIR ) # allow to change current dir
    if dlg.ShowModal() == wx.ID_OK:
      path = dlg.GetPath()
      self._load_db( path )
    dlg.Destroy()

  def on_filter( self, event ):
    r = self.curr>=0 and self.records[ self.curr ] or None
    dlg = wx.SingleChoiceDialog( self,
      'Please select the filter to apply', 'The Filter',
      self.filter_descrs,
      wx.CHOICEDLG_STYLE )
    if dlg.ShowModal() == wx.ID_OK:
      self.filter_no = dlg.GetSelection()
      self.filter_fn = self.filters[self.filter_no]
      self.check_overdue( dont_refresh=True )
      self.refresh()
      if r:
        self._goto_rec( r )
    dlg.Destroy()

  def exit( self ):
    self.timer.Stop()
    if not self.db or not self.db.dirty:
      return
    mg = "Save changes to '%s'?" % self.db_name
    msg = wx.MessageDialog( self, mg, "Exiting", wx.YES|wx.NO )
    res = msg.ShowModal()
    msg.Destroy()
    if res == wx.ID_YES:
      self.db.save()
    self.db = None

  def on_close( self, event ): # From 'Close' and from 'X'
    self.exit()
    self.Destroy()

  def __del__(self): # just for a case
    self.exit()

  def on_info( self, event ):
    num = self.n_records
    if num == 0:
      MsgBox( self, "No records", "No statistics" )
      return
    sum = 0.0
    d = 0; d_sum = 0.0
    p = 0; p_sum = 0.0
    o = 0; o_sum = 0.0
    y_sum = {}
    for r in self.records:
      a = r.amount
      y = r.date_due.y
      if y in y_sum: y_sum[y] += a
      else: y_sum[y] = a
      sum += a
      if   r.status == ST_PENDING: p += 1; p_sum += a
      elif r.status == ST_OVERDUE: o += 1; o_sum += a
      else:                       d += 1; d_sum += a
    assert num == d + p + o
    msg = "Done: \t%d \t$%.2f\n" % (d, d_sum)
    msg += "Pending: \t%d \t$%.2f\n" % (p, p_sum)
    msg += "Overdue: \t%d \t$%.2f\n" % (o, o_sum)
    msg += "\nTotal: \t%d \t$%.2f\nMean:\t\t$%.2f\n" % (num,sum,sum/num)
    msg += "\nby years:\n"
    years = y_sum.keys()
    years.sort()
    for y in years:
      msg += " \t%d \t$%.2f\n" % (y, y_sum[y])
    MsgBox( self, msg, "Statistics" )

  def on_about( self, event ):
    MsgBox( self, NAME_VERS + " (C) Georgiy Pruss 2005-2012", NAME_VERS )

class app( wx.App ):
  def OnInit( self ):
    #wx.InitAllImageHandlers()
    import sys
    frame = WorkFrame( None, -1, NAME_VERS,
      len(sys.argv)>=2 and sys.argv[1] or "i_track.tdb" )
    self.SetTopWindow( frame )
    frame.Centre()
    frame.Show( True )
    return 1

if __name__ == "__main__":
  try:
    prog = app(0)
    prog.MainLoop()
  except ErrDB, e:
    print e
    MsgBox( None, str(e), 'Error' )

"""
0.993 Added choice-box for status and combo-box for customer/company.
      Pending/overdue is checked when starting and then each 30 seconds.

      Status is -/p/o default but if some other is present in the file,
      is taken from the file
      Companies are sorted ignoring the case but XXX and xxx will be both
      present in the list, the combo-box, and the file.

0.994 Better statistics in Info (num/sum for done/pend/overdue/total)

0.995 Statistics fixed, extended

0.996 Buttons Archive and Load added

0.997 Load works. _read_db(), db_name -> db_name, db_path

0.998 Archiving works. SimpleDB.archive, _stringify_record

0.999 Optional argument - database file. Default "i_track.tdb".
      Archive files are read-only.

1.000 Removed Achiving stuff.

1.101 Filter; .records are what shown in .lc, refresh() rereads db, filters,
      sorts, sets current item; add/edit/del set current item too. Et cetera.
      But just read/show/add/edit/del work. Some sort. Some filter. Not
      consitant. Errors in many fns. No load/save.
      Changes in SimpleDB.py - more SQL-ish.

1.102 It seems everything works.

1.103 Corrections in add_record, calculation of next invoice number.

1.104 added years 2008 2009 2010.

1.105 added years 2011 to 2019.

1.106 some fixes for RecordDlg.rec presence (also in that file too).

1.107 wx returns strings as unicode -- we convert them back to strings (in RecordDB:133)
"""
