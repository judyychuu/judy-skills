import unittest
import xml.etree.ElementTree as ET
from check_shape_bounds import audit_geometry


def geometry(commands):
    return ET.fromstring('<a:custGeom xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:pathLst><a:path w="100" h="100">' + commands + '</a:path></a:pathLst></a:custGeom>')


def move(x,y):
    return f'<a:moveTo><a:pt x="{x}" y="{y}"/></a:moveTo>'


def line(x,y):
    return f'<a:lnTo><a:pt x="{x}" y="{y}"/></a:lnTo>'


class BoundsTests(unittest.TestCase):
    def test_legitimate_origin(self):
        r=audit_geometry(geometry(move(0,0)+line(100,0)+line(100,100)+'<a:close/>'))
        self.assertNotIn('issue',r)
    def test_unused_origin(self):
        r=audit_geometry(geometry(move(0,0)+move(40,40)+line(100,40)+line(100,100)+'<a:close/>'))
        self.assertEqual(r['issue'],'isolated_move_expands_bounds')
    def test_disconnected_drawn_subpaths(self):
        r=audit_geometry(geometry(move(0,0)+line(10,10)+move(50,50)+line(100,100)))
        self.assertNotIn('issue',r)
    def test_padding_requires_review_not_rewrite(self):
        r=audit_geometry(geometry(move(40,40)+line(60,40)+line(60,60)+'<a:close/>'))
        self.assertNotIn('issue',r)
        self.assertIn('review',r)
    def test_formula_is_explicitly_unverified(self):
        r=audit_geometry(geometry(move('x1',0)+line(100,100)))
        self.assertEqual(r['review'],'symbolic_or_invalid_path_coordinates')

if __name__=='__main__':unittest.main()
