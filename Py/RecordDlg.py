#!/usr/bin/env python
from Date import Date
from SimpleDB import SimpleRecord, T_STR,T_INT,T_DATE,T_MONEY
import wx
from wx.lib.rcsizer import RowColSizer
# from ObjectDB import ObjectDB

ADD    = wx.NewId()
CANCEL = wx.NewId()

ST_OVERDUE = "overdue"
ST_PENDING = "pending"
ST_NORMAL  = ""

def _prepare_parms( parent, rec=None, inv=None ):
  parms = []
  if rec:
    for i in range( parent.NF ):
      parms.append( parent.fmt_field(rec,i) )
  else:
    for i in range(parent.NF):
      if i==0:
        parms.append( inv and str(inv) or "" )
      elif i==1 or i==5: # today or due-date
        d = Date() # today
        if i==5: d += 30
        parms.append( d.format("%a") )
      else:
        parms.append( i==6 and ST_PENDING or ST_NORMAL )
  return parms

class RecordDlg( wx.Dialog ):

  def __init__( self, parent, title, rec, def_inv, **kwds ):
    wx.Dialog.__init__( self, parent, -1, title, **kwds )
    self.parent = parent
    # create values
    parms = _prepare_parms( parent, rec, def_inv )
    # create the widgets
    layout = [('Invoice:',0,1,1,-3), # lbl, txt, row, col, -colspan or flg
      ("Date Done (M/D/Y): ",1,2,1),
      ("Date Due (M/D/Y): ",5,2,3,wx.ALIGN_RIGHT),
      ("Company:",2,3,1,-3),
      ("Description:",3,4,1,-3),
      ("Amount:",4,5,1),
      ("Status: ",6,5,3,wx.ALIGN_RIGHT)]
    self.layout = layout
    self.lbl = []
    self.txt = []
    self.rec = None
    p6choices = [ST_NORMAL, ST_PENDING, ST_OVERDUE]
    p3choices = parent.companies.keys()
    p3choices.sort( lambda x,y: cmp( x.upper(), y.upper() ) )
    for i,m in enumerate(layout):
      self.lbl.append( wx.StaticText( self, -1, m[0] ) )
      p_txt = parms[m[1]]
      if i==3:
        tc = wx.ComboBox( self, -1, p_txt, choices = p3choices, style = wx.CB_DROPDOWN )
      elif i==6:
        tc = wx.Choice( self, -1, choices=p6choices )
        if p_txt in p6choices:
          tc.SetSelection( p6choices.index(p_txt) )
        else:
          tc.Append( p_txt )
          tc.SetSelection( len(p6choices) ) # after last = newly added item
      else:
        tc = wx.TextCtrl( self, -1, p_txt )
      self.txt.append( tc )
    self.butsave = wx.Button( self, ADD, "OK" )
    self.butcancel = wx.Button( self, CANCEL, "Cancel" )
    self.txt[3].SetSize( (300, 21) )
    self.txt[4].SetSize( (300, 21) )
    self.txt[4].SetMaxLength( 200 )

    self._do_layout(layout)

    self.txt[1].Bind( wx.EVT_KILL_FOCUS, self.on_kill_focus )
    self.Bind( wx.EVT_CLOSE, self.cancel )

  def _do_layout(self,layout):

    self.SetPosition( [300,250] )
    boxl = RowColSizer()
    for i,m in enumerate(layout):
      if len(m)==5 and m[4]>0:
        boxl.Add( self.lbl[i], row=m[2], col=m[3], flag=m[4] )
      else:
        boxl.Add( self.lbl[i], row=m[2], col=m[3] )
      if len(m)==5 and m[4]<0:
        boxl.Add( self.txt[i], row=m[2], col=m[3]+1, colspan=-m[4] )
      else:
        boxl.Add( self.txt[i], row=m[2], col=m[3]+1 )
    boxb = wx.BoxSizer( wx.HORIZONTAL )
    CVH = wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL
    boxb.Add( self.butsave, 0, CVH, 0 )
    boxb.Add( (50,10), 0 )
    boxb.Add( self.butcancel, 0, CVH, 0 )
    boxl.Add( boxb, row=6, col=2, colspan=3 )

    #for x in range( 1,6 ):
    #  boxl.AddSpacer( 75, 30, pos=(x,1) ) # ?
    #  boxl.AddSpacer( 50, 1, pos=(x,2) )
    boxl.AddSpacer( 0, 35, pos=(5,1) ) # row 5 col 1 - x 0 y 35
    boxl.AddSpacer( 35, 50, pos=(6,5) )

    self.SetAutoLayout( True )
    self.SetSizer( boxl )
    boxl.Fit( self )
    boxl.SetSizeHints( self )
    self.Layout()
    wx.EVT_BUTTON( self, ADD, self.add )
    wx.EVT_BUTTON( self, CANCEL, self.cancel )

  def on_kill_focus( self, event ):
    event.Skip()
    s = self.txt[1].GetValue().strip()
    try:
      m,d,y = s.split('/')
      d = Date( int(y),int(m),int(d) )
      self.txt[2].SetValue( (d+30).format( "%a") )
    except:
      pass

  def cancel( self,event ):
    self.EndModal(0)

  def add( self, event ):
    self.rec = SimpleRecord()
    try:
      for i,m in enumerate(self.layout):
        fld = m[1]
        if i==6:
          val = self.txt[i].GetStringSelection()
        else:
          val = self.txt[i].GetValue().strip()
        val = str(val) # new wx returns all as unicode. let's go back to strings
        n = self.parent.names[ fld ]
        t = self.parent.types[ fld ]
        if   t == T_INT:   val = int(val)
        elif t == T_DATE:  val = s_to_d(val)
        elif t == T_MONEY: val = s_to_m(val)
        self.rec[n] = val
    except Exception, e:
      error = wx.MessageDialog( self, str(e), 'Error', wx.OK )
      error.ShowModal()
      error.Destroy()
      return
    self.EndModal(1)

def s_to_m( s ):
  """Helper fn - convert money (e.g. 'NNN.NN' or '$NNN.NN') to float"""
  try:
    if s.startswith('$'): return float( s[1:] )
    return float(s)
  except:
    raise Exception( "invalid money format: " + s )

def s_to_d( s ):
  """Helper fn - convert data string ('M/D/Y') to my Date value"""
  try:
    m,d,y = s.split('/')
    return Date(int(y),int(m),int(d))
  except:
    raise Exception( "invalid date format: " + s + "; must be M/D/Y" )

"""
20050403-2320 Choice-box for status, combo-box for companies/customers
"""

# EOF
