#!/usr/bin/env python3
"""Read-only freeform bounds audit; numeric line and Bezier paths only."""
import argparse
import json
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'


def audit_geometry(geometry):
    """Use drawn points/control hull, never count isolated moveTo points as drawn.

    Bezier control hulls are conservative: a gap outside the hull is real,
    but absence of a gap does not prove tight curve bounds. Padding is review
    information because icons may intentionally use consistent-size viewports.
    """
    drawn, isolated = [], []
    for path in geometry.findall('./' + A + 'pathLst/' + A + 'path'):
        try:
            width, height = float(path.get('w')), float(path.get('h'))
            if width <= 0 or height <= 0:
                return {'review': 'nonpositive_path_viewport'}
            points, unused = [], []
            current, start, pending = None, None, None
            for cmd in path:
                kind = cmd.tag.removeprefix(A)
                pts = [(float(p.get('x')) / width, float(p.get('y')) / height)
                       for p in cmd.findall(A + 'pt')]
                if kind == 'moveTo' and len(pts) == 1:
                    if pending is not None:
                        unused.append(pending)
                    current = start = pending = pts[0]
                elif kind in ('lnTo', 'quadBezTo', 'cubicBezTo'):
                    expected = {'lnTo': 1, 'quadBezTo': 2, 'cubicBezTo': 3}[kind]
                    if current is None or len(pts) != expected:
                        return {'review': 'malformed_path'}
                    points.extend([current] + pts)
                    current, pending = pts[-1], None
                elif kind == 'close':
                    if current is not None and start is not None and pending is None:
                        points.extend([current, start])
                        current = start
                else:
                    return {'review': 'unsupported_path_command:' + kind}
            if pending is not None:
                unused.append(pending)
            if path.get('fill') == 'none' and path.get('stroke') in ('0', 'false'):
                continue
            drawn.extend(points)
            isolated.extend(unused)
        except (TypeError, ValueError):
            return {'review': 'symbolic_or_invalid_path_coordinates'}
    if not drawn:
        return {'review': 'no_drawn_segments'}
    xmin, xmax = min(p[0] for p in drawn), max(p[0] for p in drawn)
    ymin, ymax = min(p[1] for p in drawn), max(p[1] for p in drawn)
    # Ignore tiny coordinate rounding; do not outlaw a legitimate (0, 0).
    outside = [p for p in isolated if p[0] < xmin - 1e-6 or p[0] > xmax + 1e-6
               or p[1] < ymin - 1e-6 or p[1] > ymax + 1e-6]
    result = {'control_hull': [xmin, ymin, xmax, ymax]}
    if outside:
        result['issue'] = 'isolated_move_expands_bounds'
        result['isolated_points'] = outside
    margins = []
    if xmax - xmin > 1e-6:
        margins.extend([xmin, 1 - xmax])
    if ymax - ymin > 1e-6:
        margins.extend([ymin, 1 - ymax])
    if margins and max(margins) > 0.25:
        result['review'] = 'large_viewport_padding_check_design_intent'
    return result


def inspect(filename):
    issues, reviews, checked = [], [], 0
    with ZipFile(filename) as package:
        bad = package.testzip()
        if bad:
            raise ValueError('Corrupt ZIP member: ' + bad)
        for name in package.namelist():
            if not (name.startswith('ppt/slides/slide') and name.endswith('.xml')):
                continue
            root = ET.fromstring(package.read(name))
            for shape in root.iter():
                if shape.tag not in (P + 'sp', P + 'cxnSp'):
                    continue
                geometry = shape.find('./' + P + 'spPr/' + A + 'custGeom')
                if geometry is None:
                    continue
                checked += 1
                identity = next(shape.iter(P + 'cNvPr'), None)
                context = dict(part=name, shape_id=identity.get('id') if identity is not None else None,
                               shape_name=identity.get('name') if identity is not None else None)
                result = audit_geometry(geometry)
                if 'issue' in result:
                    issues.append(dict(context, **result))
                elif 'review' in result:
                    reviews.append(dict(context, **result))
    return dict(passed=not issues, checked_shapes=checked, issues=issues, reviews=reviews,
                scope='Numeric freeform paths; Bezier control hull only. Reviews require visual assessment. '
                      'No exact curve/arc bounds, stroke/effect extents, group/rotation transforms or application selection test. '
                      'Read-only; no geometry or gradient rewriting.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pptx')
    args = parser.parse_args()
    try:
        report = inspect(args.pptx)
    except Exception as exc:
        report = dict(passed=False, error=str(exc))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if report['passed'] else 1)
