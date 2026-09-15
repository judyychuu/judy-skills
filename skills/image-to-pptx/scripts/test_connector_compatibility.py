"""Synthetic XML fixtures; no user presentations or business content are bundled."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile
from check_connector_compatibility import inspect

NS = ('xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"')
CUSTOM = ('<a:custGeom><a:pathLst><a:path w="100" h="100" fill="none">'
          '<a:moveTo><a:pt x="0" y="100"/></a:moveTo>'
          '<a:lnTo><a:pt x="0" y="0"/></a:lnTo>'
          '<a:lnTo><a:pt x="100" y="0"/></a:lnTo>'
          '</a:path></a:pathLst></a:custGeom>')
ARROW = '<a:ln><a:prstDash val="dash"/><a:tailEnd type="triangle"/></a:ln>'


def connector(geometry=CUSTOM, ident=7):
    return (f'<p:cxnSp><p:nvCxnSpPr><p:cNvPr id="{ident}" name="Test arrow"/>'
            '<p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>'
            f'<p:spPr>{geometry}{ARROW}</p:spPr></p:cxnSp>')


def freeform():
    return ('<p:sp><p:nvSpPr><p:cNvPr id="7" name="Test arrow"/>'
            '<p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr>{CUSTOM}{ARROW}</p:spPr></p:sp>')


class ConnectorCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'fixture.pptx'

    def package(self, body, part='ppt/slides/slide1.xml'):
        # Minimal OPC test container: only the XML parts inspected by this guard.
        root = {'slides': 'sld', 'slideMasters': 'sldMaster',
                'slideLayouts': 'sldLayout'}[part.split('/')[1]]
        xml = f'<p:{root} {NS}><p:cSld><p:spTree>{body}</p:spTree></p:cSld></p:{root}>'
        with ZipFile(self.path, 'w') as z:
            z.writestr(part, xml)
        return inspect(self.path)

    def test_rejects_custom_path_connector_with_identity(self):
        r = self.package(connector())
        self.assertFalse(r['passed'])
        self.assertEqual(r['checked_connectors'], 1)
        self.assertEqual(r['issues'][0]['kind'], 'custom_geometry_in_connector')
        self.assertEqual(r['issues'][0]['shape_id'], '7')
        self.assertEqual(r['issues'][0]['shape_name'], 'Test arrow')

    def test_accepts_native_connector_presets(self):
        for preset in ('line', 'bentConnector3', 'curvedConnector3'):
            with self.subTest(preset=preset):
                r = self.package(connector(f'<a:prstGeom prst="{preset}"><a:avLst/></a:prstGeom>'))
                self.assertTrue(r['passed'])
                self.assertEqual(r['checked_connectors'], 1)

    def test_accepts_same_path_as_freeform_arrow(self):
        self.assertTrue(self.package(freeform())['passed'])

    def test_catches_nested_and_multiple_bad_connectors(self):
        r = self.package('<p:grpSp>' + connector() + '<p:grpSp>' + connector(ident=9)
                         + '</p:grpSp>' + freeform() + '</p:grpSp>')
        self.assertEqual([i['shape_id'] for i in r['issues']], ['7', '9'])

    def test_checks_masters_and_layouts(self):
        for part in ('ppt/slideMasters/slideMaster1.xml', 'ppt/slideLayouts/slideLayout1.xml'):
            with self.subTest(part=part):
                r = self.package(connector(), part)
                self.assertEqual(r['issues'][0]['part'], part)
                self.assertFalse(r['passed'])

    def test_check_does_not_mutate_file(self):
        self.package(connector())
        before = self.path.read_bytes()
        inspect(self.path)
        self.assertEqual(before, self.path.read_bytes())

    def test_cli_status_and_json(self):
        script = Path(__file__).with_name('check_connector_compatibility.py')
        for body, status in ((connector(), 1), (freeform(), 0)):
            with self.subTest(status=status):
                self.package(body)
                result = subprocess.run([sys.executable, str(script), str(self.path)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, status)
                self.assertEqual(json.loads(result.stdout)['passed'], status == 0)

    def test_cli_rejects_unreadable_package(self):
        self.path.write_bytes(b'not a zip')
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('check_connector_compatibility.py')),
                                 str(self.path)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)['passed'])


if __name__ == '__main__':
    unittest.main()
