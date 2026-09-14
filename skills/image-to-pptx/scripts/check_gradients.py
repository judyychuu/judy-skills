#!/usr/bin/env python3
"""Read-only, targeted DrawingML gradient checks; not a full OOXML validator."""
import argparse
import json
import re
import sys
from zipfile import ZipFile, BadZipFile
from xml.etree import ElementTree as ET

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
FILLS = {'noFill', 'solidFill', 'gradFill', 'blipFill', 'pattFill', 'grpFill'}
COLORS = {'srgbClr', 'scrgbClr', 'hslClr', 'sysClr', 'schemeClr', 'prstClr'}
RANK = {'xfrm': 0, 'prstGeom': 1, 'custGeom': 1,
        **{k: 2 for k in FILLS}, 'ln': 3, 'effectLst': 4, 'effectDag': 4,
        'scene3d': 5, 'sp3d': 6, 'extLst': 7}

def local(node):
    return node.tag.rsplit('}', 1)[-1]

def check(filename):
    issues, gradients = [], []
    def fail(part, index, kind, detail):
        issues.append(dict(part=part, gradient=index, kind=kind, detail=detail))
    def number(value, lo, hi):
        try:
            n = int(value)
            return n if lo <= n <= hi else None
        except (ValueError, TypeError):
            return None
    try:
        with ZipFile(filename) as z:
            for part in sorted(z.namelist()):
                if not (part.startswith('ppt/') and part.endswith('.xml')):
                    continue
                root = ET.fromstring(z.read(part))
                parents = {child: parent for parent in root.iter() for child in parent}
                for index, g in enumerate(root.iter(A + 'gradFill'), 1):
                    parent = parents.get(g)
                    if parent is not None and parent.tag in {P+'spPr', A+'spPr', P+'grpSpPr', A+'grpSpPr'}:
                        children = [local(e) for e in parent if e.tag.startswith(A)]
                        ranks = [RANK[n] for n in children if n in RANK]
                        if ranks != sorted(ranks):
                            fail(part,index,'shape_property_order',children)
                        if sum(n in FILLS for n in children) != 1:
                            fail(part,index,'conflicting_shape_fills',children)
                    children = list(g)
                    names = [local(e) for e in children]
                    gs_lists = g.findall(A+'gsLst')
                    if len(gs_lists) != 1 or not children or children[0].tag != A+'gsLst':
                        fail(part,index,'gradient_stop_list_order',names)
                    if names.count('lin') + names.count('path') > 1:
                        fail(part,index,'conflicting_gradient_directions',names)
                    if 'tileRect' in names and any(names.index(n)>names.index('tileRect') for n in ['lin','path'] if n in names):
                        fail(part,index,'gradient_direction_order',names)
                    stops = [] if not gs_lists else gs_lists[0].findall(A+'gs')
                    if len(stops)<2:
                        fail(part,index,'too_few_gradient_stops',len(stops))
                    positions=[]; colors=[]
                    for stop in stops:
                        pos=number(stop.get('pos'),0,100000)
                        if pos is None: fail(part,index,'invalid_stop_position',stop.get('pos'))
                        else: positions.append(pos)
                        cs=[c for c in stop if c.tag.startswith(A) and local(c) in COLORS]
                        if len(cs)!=1:
                            fail(part,index,'invalid_stop_color_count',len(cs));continue
                        c=cs[0];colors.append({'type':local(c),'value':c.get('val')})
                        if c.tag==A+'srgbClr' and not re.fullmatch('[0-9a-fA-F]{6}',c.get('val','')):
                            fail(part,index,'invalid_rgb',c.get('val'))
                        for alpha in c.findall(A+'alpha'):
                            if number(alpha.get('val'),0,100000) is None:
                                fail(part,index,'invalid_alpha',alpha.get('val'))
                    if positions!=sorted(positions):
                        fail(part,index,'unordered_gradient_stops',positions)
                    lin=g.find(A+'lin')
                    if lin is not None and lin.get('ang') is not None and number(lin.get('ang'),0,21599999) is None:
                        fail(part,index,'invalid_gradient_angle',lin.get('ang'))
                    gradients.append(dict(part=part,gradient=index,positions=positions,colors=colors,
                                          direction= 'linear' if lin is not None else 'path' if g.find(A+'path') is not None else 'inherited'))
    except (OSError, BadZipFile, ET.ParseError) as exc:
        fail(str(filename),None,'unreadable_package',str(exc))
    return dict(passed=not issues,gradient_count=len(gradients),issues=issues,gradients=gradients,
                scope='Targeted gradient structure checks only; no theme resolution, full schema validation, source color matching or PowerPoint rendering verification.')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('pptx');args=ap.parse_args()
    report=check(args.pptx);print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(0 if report['passed'] else 1)
