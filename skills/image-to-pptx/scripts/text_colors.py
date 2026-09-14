#!/usr/bin/env python3
"""Audit or materialize slide paragraph colors onto runs. Requires lxml.
Never overwrites input; unresolved colors are reported, not guessed.
"""
import argparse
import copy
import json
from pathlib import Path
import re
from zipfile import ZipFile
from lxml import etree as ET

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NS = {'a': A}
FILL_NAMES = ('noFill', 'solidFill', 'gradFill', 'blipFill', 'pattFill', 'grpFill')
FILL_TAGS = {f'{{{A}}}{x}' for x in FILL_NAMES}

def fill_of(props):
    fills = [] if props is None else [x for x in props if x.tag in FILL_TAGS]
    if len(fills) > 1:
        raise ValueError('Multiple conflicting fills on one text property element')
    return fills[0] if fills else None

def insert_fill(props, fill):
    # CT_TextCharacterProperties: line, fill, effects, fonts, ...
    at = 1 if len(props) and props[0].tag == f'{{{A}}}ln' else 0
    props.insert(at, copy.deepcopy(fill))

def process(source, output=None):
    source = Path(source)
    if output is not None:
        output = Path(output)
        if output.resolve() == source.resolve() or output.exists():
            raise ValueError('Output must be a new file distinct from input')
    findings, changed, roots = [], 0, {}
    with ZipFile(source) as z:
        if z.testzip():
            raise ValueError('Corrupt package')
        for name in z.namelist():
            if not re.fullmatch(r'ppt/slides/slide\d+\.xml', name):
                continue
            root = ET.fromstring(z.read(name))
            for idx, para in enumerate(root.iter(f'{{{A}}}p')):
                runs = [r for r in para if r.tag in (f'{{{A}}}r', f'{{{A}}}fld') and r.find('a:t', NS) is not None]
                if not runs:
                    continue
                default = para.find('a:pPr/a:defRPr', NS)
                fallback = fill_of(default)
                if fallback is not None:
                    findings.append(dict(part=name, paragraph=idx, kind='paragraph_color_fallback'))
                safe = True
                for run in runs:
                    props = run.find('a:rPr', NS)
                    direct = fill_of(props)
                    if direct is None and fallback is None:
                        safe = False
                        findings.append(dict(part=name, paragraph=idx, kind='unresolved_style_color'))
                    elif direct is None and output is not None:
                        if props is None:
                            props = ET.Element(f'{{{A}}}rPr')
                            run.insert(0, props)
                        insert_fill(props, fallback)
                        changed += 1
                if fallback is not None and safe and output is not None:
                    # Keep new typing consistent with original paragraph color.
                    end = para.find('a:endParaRPr', NS)
                    if end is None:
                        end = ET.SubElement(para, f'{{{A}}}endParaRPr')
                    if fill_of(end) is None:
                        insert_fill(end, fallback)
                    for br in para.findall('a:br', NS):
                        bp = br.find('a:rPr', NS)
                        if bp is None:
                            bp = ET.SubElement(br, f'{{{A}}}rPr')
                        if fill_of(bp) is None:
                            insert_fill(bp, fallback)
                    default.remove(fallback)
            roots[name] = root
        unresolved = [x for x in findings if x['kind'] == 'unresolved_style_color']
        if output is not None and unresolved:
            raise ValueError('Unresolved master/layout/theme color: resolve in generation source; no output written')
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            with ZipFile(output, 'w') as dst:
                for info in z.infolist():
                    body = z.read(info.filename)
                    if info.filename in roots:
                        body = ET.tostring(roots[info.filename], encoding='UTF-8', xml_declaration=True, standalone=True)
                    dst.writestr(info, body)
    return dict(findings=findings, materialized_runs=changed,
                output=str(output) if output else None,
                scope='Color structure only; fallback is legal OOXML, not proof of an application bug. No UI/copy/paste certification.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('--output', help='Explicitly request a new normalized copy')
    args = parser.parse_args()
    try:
        print(json.dumps(process(args.input, args.output), ensure_ascii=False, indent=2))
    except Exception as exc:
        parser.exit(1, str(exc)+'\n')
