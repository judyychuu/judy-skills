#!/usr/bin/env python3
"""Reject emoji and text arrows in editable PPTX text; allow native list bullets."""
import sys,json,zipfile,xml.etree.ElementTree as E
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
def prohibited(c):
 n=ord(c)
 return (0x2190<=n<=0x21ff or 0x2600<=n<=0x27bf or 0x27f0<=n<=0x27ff or 0x2900<=n<=0x297f or 0x2b00<=n<=0x2bff or 0x1f000<=n<=0x1faff or n in (0xfe0f,0x20e3))
def check(path):
 issues=[]
 with zipfile.ZipFile(path) as z:
  for name in z.namelist():
   if not name.startswith('ppt/') or not name.endswith('.xml'):continue
   root=E.fromstring(z.read(name))
   for e in root.iter(A+'t'):
    t=e.text or '';bad=sorted(set(c for c in t if prohibited(c)))
    if bad:issues.append({'part':name,'text':t,'codepoints':['U+%04X'%ord(c) for c in bad]})
   for e in root.iter():
    f=e.get('typeface','').lower()
    if any(x in f for x in ('emoji','wingdings','webdings','segoe mdl2','segoe fluent icons')):issues.append({'part':name,'symbol_font':f})
 return {'passed':not issues,'issues':issues,'scope':'Text arrows, common emoji ranges and symbol fonts; does not inspect raster/SVG artwork or prove application rendering.'}
if __name__=='__main__':
 r=check(sys.argv[1]);print(json.dumps(r,ensure_ascii=False,indent=2));sys.exit(0 if r['passed'] else 1)
