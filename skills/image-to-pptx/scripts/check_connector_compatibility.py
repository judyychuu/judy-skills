#!/usr/bin/env python3
"""Read-only check for custom-path connectors known to trigger PowerPoint repair.

This is a targeted application-compatibility guard, not an OOXML schema validator.
The affected combination can be schema-valid and render in other applications.
"""
import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
PART = re.compile(r'^ppt/(?:slides|slideMasters|slideLayouts)/[^/]+\.xml$')


def inspect(filename):
    issues, checked, parts = [], 0, 0
    with ZipFile(filename) as package:
        bad = package.testzip()
        if bad:
            raise ValueError('Corrupt ZIP member: ' + bad)
        for name in package.namelist():
            if not PART.fullmatch(name):
                continue
            root = ET.fromstring(package.read(name))
            parts += 1
            # iter includes connectors nested in groups.
            for connector in root.iter(P + 'cxnSp'):
                checked += 1
                if connector.find('./' + P + 'spPr/' + A + 'custGeom') is None:
                    continue
                identity = connector.find('./' + P + 'nvCxnSpPr/' + P + 'cNvPr')
                issues.append(dict(
                    part=name,
                    shape_id=identity.get('id') if identity is not None else None,
                    shape_name=identity.get('name') if identity is not None else None,
                    kind='custom_geometry_in_connector',
                    action='Use a preset connector, or regenerate the custom path as p:sp '
                           'with matching p:nvSpPr/p:cNvSpPr and native arrow ends. '
                           'Preserve geometry and line styling; verify in PowerPoint.'
                ))
    return dict(
        passed=not issues, checked_parts=parts, checked_connectors=checked, issues=issues,
        scope='Only detects p:cxnSp/p:spPr/a:custGeom in slides, masters and layouts, '
              'including groups. Does not validate the whole package or prove rendering, '
              'editing, save/reopen or cross-deck copying. Read-only; no file rewriting.'
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pptx')
    args = parser.parse_args()
    try:
        report = inspect(args.pptx)
    except Exception as exc:
        report = dict(passed=False, error=str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
