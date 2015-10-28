#!/usr/bin/env python
from Date import Date
from SimpleDB import SimpleRecord, T_STR,T_INT,T_DATE,T_MONEY
import wx
from wx.lib.rcsizer import RowColSizer
# from ObjectDB import ObjectDB

F1 = wx.NewId()
F2 = wx.NewId()
F3 = wx.NewId()
F4 = wx.NewId()

class FilterDlg( wx.Dialog ):

  def __init__( self, parent, id, title, **kwds ):
    wx.Dialog.__init__( self, parent, id, title, **kwds )
    self.parent = parent
    # create the widgets
    layout = [('F1:',0,1,1), # lbl, txt, row, col, -colspan or flg
              ("F2:",1,2,1),
              ("F3:",2,3,1)]
    self.layout = layout
    self.lbl = []
    self.txt = []
    for i,m in enumerate(layout):
      self.lbl.append( wx.StaticText( self, -1, m[0] ) )
      p_txt = ".."
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
    #print self.rec.__dict__
    self.EndModal(1)

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
    m,d,y = s.split('/')
    return Date(int(y),int(m),int(d))
  except:
    raise Exception( "invalid date format: " + s )

"""
20050403-2320 Choice-box for status, combo-box for companies/customers
"""

# EOF
