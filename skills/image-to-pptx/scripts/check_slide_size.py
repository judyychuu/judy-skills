#!/usr/bin/env python3
"""Read-only comparison of generated and target PPTX slide dimensions in EMU."""
import argparse
import json
import sys
import xml.etree.ElementTree as ET
from zipfile import ZipFile


def dimensions(path):
    with ZipFile(path) as package:
        root = ET.fromstring(package.read('ppt/presentation.xml'))
    node = root.find('{http://schemas.openxmlformats.org/presentationml/2006/main}sldSz')
    if node is None:
        raise ValueError('Missing p:sldSz')
    width, height = int(node.attrib['cx']), int(node.attrib['cy'])
    if width <= 0 or height <= 0:
        raise ValueError('Slide dimensions must be positive')
    return {'width_emu': width, 'height_emu': height}


def inspect(generated, template):
    actual, target = dimensions(generated), dimensions(template)
    return {
        'passed': actual == target,
        'generated': actual,
        'template': target,
        'target_to_generated_scale': {
            'x': target['width_emu'] / actual['width_emu'],
            'y': target['height_emu'] / actual['height_emu'],
        },
        'scope': 'Exact slide size only; does not verify copy/paste, fonts or rendering',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pptx')
    parser.add_argument('--template', required=True)
    args = parser.parse_args()
    try:
        result = inspect(args.pptx, args.template)
    except (OSError, ValueError, KeyError, ET.ParseError) as exc:
        result = {'passed': False, 'error': str(exc)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
