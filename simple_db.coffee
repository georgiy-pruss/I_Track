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
  ((unescape2(s) for s in line.split(sep)) for line in lines when line.indexOf(sep) > 0)

write_db = (filename,recs) ->
  txt = ((escape2(s) for s in rec).join(';') for rec in recs when rec.length>1).join('\n')
  fs.writeFileSync(filename,txt)

writepage = (res,txt) ->
    bytelen = (unescape encodeURIComponent txt).length
    res.writeHead 200, {'Content-Type': 'text/html', 'Content-Length': bytelen}
    res.end txt

show_db = (res, recs) ->
  text = "<html><body><p><a href='/help'>help</a> <a href='/quit'>quit</a></p><table>"
  header = recs[0]
  text += "<thead style='background-color:#CCC'>"
  for field in header
    text += "<th>#{field.split(':')[0]}</th>"
  text += "</thead>"
  for rec in recs[1..]
    clr = if rec[rec.length-1]=='overdue' then ' style="color:red"' else ''
    text += "<tr#{clr}>"
    for field in rec
      text += "<td>#{field}</td>"
    text += "</tr>"
  text += "</table></body></html>"
  writepage res,text

recs = read_db "i_track.tdb"

listener = (req, res) ->
  if req.method != 'GET' then return
  if req.url=='/quit'
    writepage res, 'Goodbye, Root!'; process.exit()
  else if req.url=='/show'
    show_db res, recs
  else if req.url=='/help'
    writepage res,"Commands: show help quit"
  else
    writepage res,"wrong request"

http.createServer( listener ).listen 8000
