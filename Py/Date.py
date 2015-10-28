# Date.py
# encoding: cp1251

import time # for Date()

"""
frac( x )               -- fractional part       5.678 -> 0.678
hms2d( h,m,s )          -- time as part of day   6,0,0 -> 0.25
d2hms( d )              -- part of day to HMS    0.25 -> 6,0,0.0
y2l( y )                -- ool*, is leap year    2000 -> True
ym2n( y,m )             -- number of days in y,m 2000,2 -> 29
ymd2j( y,m,d )          -- mod.julian day        2000,1,1.99 -> 51544.99
ut2j( u )               -- unix time to MJD      1e9 -> ... 2001.9.9.1:46:40
j2wd( j )               -- week day              51544 -> 6 (2001.1.1 Sat)
j2mp( j )               -- moon phase (0..29.5)  53446 -> 6.44
j2ut( j )               -- unix time             40587 -> 0 (1970.1.1)
j2jmd( j )              -- MJD to Y,M,D          51544 -> 2000,1,1
ymdhms2d( y,m,d,h,n,s ) -- date+time to MJD
j2ymdhms( j )           -- MDJ to date+time
Date class              -- see below
"""

def frac(x):
  return x - int(x)

def hms2d( h, m, s ):
  return (h + m/60.0 + s/3600.0)/24.0

def d2hms( d ): # d < 1.0
  d *= 24.0;  h = int(d);  d -= h
  d *= 60.0;  m = int(d);  d -= m
  return h, m, 60.0*d

def y2l( y ):
  return y%4 == 0 and y%100 != 0 or y%400 == 0

def ym2n( y, m ):
  if m in (4,6,9,11): return 30
  if m==2: return y2l(y) and 29 or 28
  return 31

def ymd2j( y, m, d ):
  c = 0
  if m <= 2:
    m += 12
    y -= 1
  if y > 1582: # for Gregorian only (we use 1 Mar 1583 as the first Greg. day
    a = y//100
    c = 2 - a + a//4
  e = int( 365.25 * (y + 4716) ) - 2401525
  f = (m + 1) * 153 // 5 + c # * 30.6
  return e + f + d

def ut2j( u ):
  return u/86400.0 + 40587.0

def j2wd( j ):
  return int(j + 3) % 7

def j2mp( j ):
  return (j + 10.8103081) % 29.53058868 # +-1.5

def j2ut( j ):
  return (j - 40587) * 86400

def j2ymd( j ): # j -> y,m,d
  # double b,f,e
  j += 2400001.0
  b = int( j ) # b -- whole part
  f = j - b    # f -- frac. part
  if j >= 2299298.0: # Gregorian
    w = int( (b - 1867216.25) / 36524.25 )
    b += 1.0 + w - w//4
  b += 1524.0
  c = int( (b - 122.1) / 365.25 )
  b -= int( 365.25 * c )
  e = int( b / 30.6001 )
  m = e>13 and e-13 or e-1
  y = e>13 and c-4715 or c-4716
  return y, m, b - int( 30.6001*e ) + f

def ymdhms2j( y,m,d,h,n,s ): # y,m,d,H,M,S -> j
  return ymd2j( y,m,d + hms2d(h,n,s))

def j2ymdhms( j ): # j -> y,m,d,H,M,S
  y,m,d = j2ymd( j )
  h,n,s = d2hms( frac(d) )
  return y,m,int(d),h,n,s

FULL_MONTHS = ['January','February','March','April','May','June','July',
               'August','September','October','November','December']
FULL_WKDAYS = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
MONTHS = 'JanFebMarAprMayJunJulAugSepOctNovDec'
WKDAYS = 'SunMonTueWedThuFriSat'

def s2ymd( s, fmt='' ): # parse string to y,m,d
  # ignore fmt for now, will be implemented later
  r = '/' in s and '/' or '.' in s and '.' or '-' in s and '-' or ' '
  a = s.split(r)
  assert len(a) == 3
  a = [int(x) for x in a] # convert all three components to int
  # M/D/Y or D.M.Y or Y M D or Y-M-D
  a = r=='/' and (a[2],a[0],a[1]) or r=='.' and (a[2],a[1],a[0]) or a
  return a

def ymd2s( s, y, m, d ): return _jymd2s( s, ymd2j( y,m,d ), y,m,d )

def j2s( s, j ): return _jymd2s( s, j, *j2ymd(j) )

def _year_day(j,y): return j - ymd2j( y,1,0 )

def _jymd2s( s, j, y,m,d ):
  r = ''
  p = s.find('%')
  while p>=0:
    r += s[:p] # move all before '%'
    t = s[p+1:p+5] # max 4 chars
    if t.startswith('%'):      r += '%';                    x = 2
    elif t.startswith('D'):    r += '%02d'%d;               x = 2
    elif t.startswith('M'):    r += '%02d'%m;               x = 2
    elif t.startswith('Y'):    r += '%04d'%y;               x = 2
    elif t.startswith('dd'):   r += '%02d'%d;               x = 3
    elif t.startswith('d'):    r += '%d'%d;                 x = 2
    elif t.startswith('mmmm'): r += FULL_MONTHS[m-1];       x = 5
    elif t.startswith('mmm'):  r += MONTHS[3*(m-1):][:3];   x = 4
    elif t.startswith('mm'):   r += '%02d'%m;               x = 3
    elif t.startswith('m'):    r += '%d'%m;                 x = 2
    elif t.startswith('yyyy'): r += '%04d'%y;               x = 5
    elif t.startswith('yy'):   r += '%02d'%(y%100);         x = 3
    elif t.startswith('y'):    r += '%d'%(y%100);           x = 2
    elif t.startswith('j'):    r += '%d'%j;                 x = 2
    elif t.startswith('u'):    r += '%d'%j2ut(j);           x = 2
    elif t.startswith('wwww'): r += FULL_WKDAYS[j2wd(j)];   x = 5
    elif t.startswith('www'):  r += WKDAYS[3*j2wd(j):][:3]; x = 4
    elif t.startswith('ww'):   r += WKDAYS[3*j2wd(j):][:2]; x = 3
    elif t.startswith('w'):    r += "%d" % j2wd(j);         x = 2
    elif t.startswith('nnn'):  r += '%03d'%_year_day(j,y);  x = 4
    elif t.startswith('nn'):   r += '%02d'%_year_day(j,y);  x = 3
    elif t.startswith('n'):    r += '%d'%_year_day(j,y);    x = 2
    elif t.startswith('a'):    s = "%M/%D/%Y" + s[p+2:];    x = 0
    elif t.startswith('e'):    s = "%D.%M.%Y" + s[p+2:];    x = 0
    elif t.startswith('i'):    s = "%Y-%M-%D" + s[p+2:];    x = 0
    else: x = 1
    if x>0: s = s[p+x:]
    p = s.find('%')
  # add local date %l and %L
  return r + s


class Date:

  """
  Date() # today
  Date( y,m,d )  Date( y,m ) # Y.M.1  Date( y ) # Y.1.1
  Date( j=mjd )
  Date( u=unixtime )
  Date( '...' ) # 'y m d' or 'y-m-d' or 'm/d/y' or 'd.m.y'
  ### Date( fmt, str ) where fmt is with %yyy %y %mmm %m %d %j %u %n
  .y .m .d .j # invariant ymd2j(y,m,d)==j
  .ymd() # (y,m,d)
  .week_day() # 0 to 6 - Sun to Sat
  .year_day() # 1..366
  .unix_time() # seconds since 1970.1.1.0:0:0 (till Y.M.d.0:0:0 usually)
  .moon_phase() # 0..29.53 +- 1.5
  str() --> %yyyy.%mm.%dd
  int() --> mjd
  .format( [fmt] ) --> string (default %Y.%M.%D)
    %a - american %M/%D/%Y  %e - european %D.%M.%Y  %i - iso %Y-%M-%D
    %yyyy %yyy %yy %y - year  %mmmm %mmm %mm %m - month  %dd %d - day
    %www %ww %w - weekday  %j - mjd  %u - unixtime  % - year day
  d+d d-d d+n n+d d-n d<=>d
  ToDo: week number
  ToDo: before/around/after 1582
  """

  def __init__( self, y=0, m=1, d=1, j=None, u=None ):
    # Date(y,m,d) Date(j=...) Date(u=...) Date()
    if j is not None:
      self.j = j
      self.y, self.m, self.d = j2ymd( j )
    elif u is not None:
      self.j = ut2j( u )
      self.y, self.m, self.d = j2ymd( self.j )
    elif type(y)==str:
      self.y, self.m, self.d = a = s2ymd( y )
      self.j = ymd2j(*a)
    elif y == 0:
      self.y, self.m, self.d = a = time.localtime()[0:3]
      self.j = ymd2j(*a)
    else:
      self.y, self.m, self.d = y,m,d
      self.j = ymd2j(y,m,d)

  def __cmp__( self, other ):
    return cmp( self.j, other.j )

  def __sub__( self, other ):
    if other.__class__ in [int,float]:
      return Date( j = self.j - int(other) )
    if other.__class__ == Date:
      return self.j - other.j
    raise TypeError()

  def __add__( self, other ):
    if other.__class__ in [int,float]:
      return Date( j = self.j + int(other) )
    raise TypeError()

  def __radd__( self, other ):
    if other.__class__ in [int,float]:
      return Date( j = self.j + int(other) )
    raise TypeError()

  def __str__( self ):
    return self.format()

  def __int__( self ):
    return self.j

  def week_day( self ):
    return j2wd( self.j )

  def year_day( self ):
    return self.j - ymd2j( self.y, 1, 0 )

  def unix_time( self ):
    return j2ut( self.j )

  def moon_phase( self ):
    return j2mp( self.j )

  def format( self, s = "%Y.%M.%D" ):
    return _jymd2s( s, self.j, self.y, self.m, self.d )

  def ymd( self ):
    return (self.y, self.m, self.d)


if __name__ == '__main__':
  # day 0, unix epoche, Y2K
  assert j2ymd(0) == (1858, 11, 17.0)
  assert ymd2j(1970,1,1) == ut2j(0)
  assert ymd2j(2000,1,1) == 51544
  # ymdhms
  j = ymdhms2j(2005,1,1,23,59,59) # 53371.9999884
  assert abs( frac( j2ymdhms( j )[5] ) ) < 0.000006
  #print d2hms(0.99999) # (23, 59, 59.136)
  #h, m, s = hms2d(1,0,0), hms2d(0,1,0), hms2d(0,0,1)
  #print d2hms(h), d2hms(m), d2hms(s) # (1, 0, 0.0) (0, 1, 0.0) (0, 0, 1.0)
  if 0: # check all days
    n, w = 0, 6
    for y in range(1600,2500+1):
      for m in range(1,12+1):
        for d in range(1,ym2n(y,m)+1):
          j = ymd2j(y,m,d)
          assert j2wd(j) == w
          Y,M,D = j2ymd(j)
          if (Y,M,int(D)) != (y,m,d):
            print y,m,d,j,Y,M,D
          n += 1
          w = (w+1) % 7
    assert n == (ymd2j(2501,1,1)-ymd2j(1600,1,1)) == 329084 # days tested
  # Constructor
  assert Date(2001,1,1) == Date(2001,1) == Date(2001) == Date(j=51910)
  # Formatting
  d = Date( 2005,4,1 )
  assert str(d) == '2005.04.01' and int(d) == d.j == 53461
  assert d.format( '%%a %a %e %i' ) == '%a 04/01/2005 01.04.2005 2005-04-01'
  assert d.format( '%yyyy %yy %y %mm %m %dd %d' ) == '2005 05 5 04 4 01 1'
  assert d.format( '%w %j %u %Y %M %D' ) == '5 53461 1112313600 2005 04 01'
  assert d.format( '%mmmm %mmm %wwww %www %ww' ) == 'April Apr Friday Fri Fr'
  assert Date( 2005 ).format( '%n %nn %nnn' ) == '1 01 001'
  assert Date( 2005,3,1 ) < Date( 2005,4,1 )
  assert Date( 2005,4,1 ) - Date( 2005,3,1 ) == 31
  assert Date( 2005,4,1 ) - 31 == Date( 2005,3,1 )
  assert Date( 2005,3,1 ) + 31 == 31 + Date( 2005,3,1 ) == Date( 2005,4,1 )
  assert Date( '2005 4 1' ) == Date( '2005 04 01' )
  assert Date( '2005-4-1' ) == Date( '4/1/2005' ) == Date( '1.4.2005' )
  MONTHS = 'ЯнвФевМарАпрМайИюнИюлАвгСенОктНояДек'
  assert Date( 2000,1 ).format( '%mmm' ) == 'Янв'

  if 0: # Julian-Gregorian leap
    for d in range(17,32):
      d1 = Date( 1583,2,d )
      print d1.j, d1, Date( j=d1.j )
    for d in range(14,16):
      d1 = Date( 1583,3,d )
      print d1.j, d1, Date( j=d1.j )
    """     Julian     Gregorian
    -100705 1583.02.17 1583.02.17 =
    -100704 1583.02.18 1583.02.18 =
    -100703 1583.02.19 1583.03.01 <--.
    -100702 1583.02.20 1583.03.02    :
    -100701 1583.02.21 1583.03.03    :
    -100700 1583.02.22 1583.03.04    :
    -100699 1583.02.23 1583.03.05    :
    -100698 1583.02.24 1583.03.06    :
    -100697 1583.02.25 1583.03.07    :
    -100696 1583.02.26 1583.03.08    :
    -100695 1583.02.27 1583.03.09    :
    -100694 1583.02.28 1583.03.10    :
    -100693 1583.02.29 1583.03.11    :
    -100692 1583.02.30 1583.03.12    :
    -100691 1583.02.31 1583.03.13 <--'
    -100690 1583.03.14 1583.03.14 =
    -100689 1583.03.15 1583.03.15 =
    -100688 1583.03.16 1583.03.16 =
    """

# EOF
