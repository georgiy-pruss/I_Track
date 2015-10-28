http = require 'http'
path = require 'path'
url = require 'url'
fs = require 'fs'

unescape2 = (s) ->
  if s[0]=='"' and s[-1..]=='"'
    s = s[1...-1]
  s.replace(/%2C/g,',').replace(/%3B/g,';').replace(/%22/g,'"').replace(/%27/g,"'").replace(/%25/g,'%')

escape2 = (s) ->
  s.replace(/%/g,'%25').replace(/;/g,'%3B').replace(/"/g,'%22').replace(/'/g,"%27")


read_db = (filename) -> # read both old (with ',') and new (with ';') formats
  lines = fs.readFileSync(filename).toString().split /[\n\r]+/g
  if lines.length==0 then return null
  sep = if lines[0].split(',').length > lines[0].split(';').length then ',' else ';'
  recs = ((unescape2(s) for s in line.split(sep)) for line in lines when line.indexOf(sep) > 0)
  maxfld0 = 0
  for rec in recs
    maxfld0 = +rec[0] if +rec[0] > maxfld0
  [maxfld0, recs]


write_db = (filename,recs) ->
  txt = ((escape2(s) for s in rec).join(';') for rec in recs when rec.length>1).join('\n')
  fs.writeFileSync(filename,txt)

writepage = (res,txt) ->
  bytelen = (unescape encodeURIComponent txt).length
  res.writeHead 200, {'Content-Type': 'text/html', 'Content-Length': bytelen}
  res.end txt

scrpt = (k) ->
  if k=='add'
    """<script>function mba(){alert('G.Pruss 2015')}
    function mbh(){alert('No worry, all will be fine')}
    function sendadd(t) { alert(t) }
    </script>"""
  else
    """<script>function mba(){alert('G.Pruss 2015')}
    function mbh(){alert('No worry, all will be fine')}
    function edr(n) {alert('Edit '+n)}
    </script>"""

menu = (k) ->
  if k=='add'
    "<p><a href='javascript:ok()'>ok</a> <a href='javascript:cancel()'>cancel</a></p>\n"
  else
    "<p><a href='/info'>info</a> <a href='/add'>add</a> <a href='/edit'>edit</a> "+
    "<a href='/filter'>filter</a> <a href='/save'>save</a> <a href='/savev'>save visible</a> "+
    "<a href='/print'>print</a> <a href='javascript:mbh()'>help</a> "+
    "<a href='javascript:mba();'>about</a> <a href='/quit'>quit</a></p>\n"

add_record = (res, recs) ->
  text = """<html><head>#{scrpt('add')}</head>
    <body style='margin: 10px; padding: 0px'>\n#{menu('add')}<div class='scrl'><form>\n
    invoice: <input type='text' width=2></input><br>
    date_done: <input type='text' width=20></input><br>
    <button text='ok' onclick='sendadd(this)'>OK</button>
    </form></div></body></html>"""
  writepage res,text

show_db = (res, recs) ->
  text = """<html><head>#{scrpt('')}
    <style>body{margin:10px;padding:0px;height:95%;} td{white-space: nowrap;}
      div.scrl{height:90%;width:70%;background-color:#EFF;display:inline-block;float:left;
      overflow-y:auto;overflow-x:hidden;border:1px solid #000;} table{width:100%;}
      thead,thead tr:hover{background-color:#CCC} tr:hover{background-color:#EEF;}
    </style></head><body>\n#{menu('')}<div class='scrl'><table>\n"""
  header = recs[0]
  text += "<thead><tr>"
  for field in header
    text += "<th>#{field.split(':')[0]}</th>"
  text += "</tr></thead><tbody>\n"
  for rec in recs[1..]
    clr = if rec[rec.length-1]=='overdue' then ' style="color:red"' else ''
    text += "<tr#{clr} onclick='edr(#{rec[0]})'>"
    for field in rec
      text += "<td>#{field}</td>"
    text += "</tr>\n"
  text += "</tbody></table></div></body></html>"
  writepage res,text

[maxinvoice,recs] = read_db "i_track.tdb"

listener = (req, res) ->
  if req.method != 'GET' then return
  if req.url=='/quit'
    writepage res, 'Goodbye, Root!'; process.exit()
  else if req.url=='/show' or req.url=='/'
    show_db res, recs
  else if req.url=='/add'
    add_record res,recs
  else if req.url=='/edit'
    writepage res,"edit"
  else if req.url=='/filter'
    writepage res,"filer"
  else if req.url=='/save'
    writepage res,"save"
  else if req.url=='/savev'
    writepage res,"save visible, filtered"
  else if req.url=='/info'
    writepage res,"info #{maxinvoice}"
  else if req.url=='/print'
    writepage res,"print"
  else
    writepage res,"wrong request"

http.createServer( listener ).listen 8000
