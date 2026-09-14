#!/usr/bin/env python3
"""Read-only, conservative font-size gate for generated PPTX. Standard library only."""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'

def inspect(path):
    issues, sizes = [], set()
    runs = 0
    with ZipFile(path) as package:
        bad = package.testzip()
        if bad:
            raise ValueError('Corrupt ZIP member: ' + bad)
        for name in package.namelist():
            if not (name.startswith('ppt/') and name.endswith('.xml')):
                continue
            root = ET.fromstring(package.read(name))
            def issue(kind, **detail):
                issues.append(dict(part=name, kind=kind, **detail))
            for node in root.iter():
                if node.tag in (A+'rPr', A+'defRPr', A+'endParaRPr') and 'sz' in node.attrib:
                    raw = node.get('sz')
                    if not raw.isdigit() or int(raw) <= 0 or int(raw) % 100:
                        issue('non_integer_font_size', value=raw)
                    else:
                        sizes.add(int(raw)//100)
                if node.tag == A+'normAutofit':
                    issue('automatic_font_scaling', settings=node.attrib)
            if not re.fullmatch(r'ppt/slides/slide\d+\.xml', name):
                continue
            # Require explicit run/paragraph sizes for generated slide text.
            # Do not silently claim unresolved master/theme inheritance was checked.
            for paragraph in root.iter(A+'p'):
                default = paragraph.find('./'+A+'pPr/'+A+'defRPr')
                for run in paragraph:
                    if run.tag not in (A+'r', A+'fld'):
                        continue
                    txt = run.find(A+'t')
                    if txt is None or not txt.text:
                        continue
                    runs += 1
                    props = run.find(A+'rPr')
                    size = props.get('sz') if props is not None else None
                    if size is None and default is not None:
                        size = default.get('sz')
                    if size is None:
                        issue('unresolved_inherited_size', action='Resolve effective style and write explicit integer run size before rechecking')
            for shape in root.iter(P+'sp'):
                flags = shape.find('./'+P+'nvSpPr/'+P+'cNvSpPr')
                if flags is not None and flags.get('txBox') in ('1', 'true'):
                    body = shape.find('./'+P+'txBody/'+A+'bodyPr')
                    if body is None or body.find(A+'spAutoFit') is None:
                        issue('textbox_requires_shape_autofit')
                else:
                    text_body = shape.find(P+'txBody')
                    body = text_body.find(A+'bodyPr') if text_body is not None else None
                    # Ordinary shapes may have text frames without being text boxes.
                    # Even an empty auto-sized frame can change geometry on paste.
                    has_content = text_body is not None and (
                        any((node.text or '').strip() for node in text_body.iter(A+'t'))
                        or next(text_body.iter(A+'fld'), None) is not None
                    )
                    if not has_content and body is not None and body.find(A+'spAutoFit') is not None:
                        identity = shape.find('./'+P+'nvSpPr/'+P+'cNvPr')
                        issue('empty_graphic_shape_autofit',
                              shape_id=identity.get('id') if identity is not None else None,
                              shape_name=identity.get('name') if identity is not None else None,
                              action='Remove the empty text body or use noAutofit; preserve geometry and populated shape text')
            for group in root.iter(P+'grpSp'):
                xfrm = group.find('./'+P+'grpSpPr/'+A+'xfrm')
                if xfrm is not None:
                    ext, child = xfrm.find(A+'ext'), xfrm.find(A+'chExt')
                    if ext is not None and child is not None and ext.attrib != child.attrib:
                        issue('scaled_group_requires_review', action='Normalize group coordinates and text sizes before rechecking')
        if not runs:
            issues.append(dict(kind='no_editable_text_runs'))
    return dict(passed=not issues, text_runs=runs, declared_integer_sizes_pt=sorted(sizes), issues=issues,
                scope='DrawingML text sizes, explicit slide run sizes, autofit and group scale; not a visual or application UI test')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pptx')
    args = parser.parse_args()
    try:
        result = inspect(args.pptx)
    except Exception as exc:
        result = dict(passed=False, error=str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result['passed'] else 1)
