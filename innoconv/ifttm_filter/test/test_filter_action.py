# pylint: disable=missing-docstring

import unittest
import panflute as pf

from innoconv.ifttm_filter.filter_action import IfttmFilterAction


class TestFilterAction(unittest.TestCase):
    def test_ifttm_block_fi_else_fi(self):
        """filter() should handle block if/else/fi"""
        filter_action = IfttmFilterAction()
        doc = pf.Doc()
        blocks = [
            pf.RawBlock(r'\ifttm', format='latex'),
            pf.Para(pf.Str('foo')),
            pf.RawBlock(r'\else', format='latex'),
            pf.Para(pf.Str('bar')),
            pf.RawBlock(r'\fi', format='latex'),
        ]
        doc.content.extend(blocks)

        with self.subTest('handle ifttm'):
            elem = doc.content[0]
            ret = filter_action.filter(elem, elem.doc)
            self.assertEqual(ret, [])

        with self.subTest('handle para foo'):
            elem = doc.content[1]
            ret = filter_action.filter(elem, elem.doc)
            self.assertEqual(ret, [])

        with self.subTest('handle else'):
            elem = doc.content[2]
            ret = filter_action.filter(elem, elem.doc)
            self.assertEqual(ret, [])

        with self.subTest('handle para bar'):
            elem = doc.content[3]
            ret = filter_action.filter(elem, elem.doc)
            self.assertEqual(ret, [])

        with self.subTest('handle fi'):
            elem = doc.content[4]
            ret = filter_action.filter(elem, elem.doc)[0]
            self.assertIsInstance(ret, pf.Para)
            self.assertIsInstance(ret.content[0], pf.Str)
            self.assertEqual(ret.content[0].text, 'foo')

    def test_ifttm_block_if_fi(self):
        """filter() should handle block if/fi"""
        filter_action = IfttmFilterAction()
        doc = pf.Doc()
        blocks = [
            pf.RawBlock(r'\ifttm', format='latex'),
            pf.Para(pf.Str('foo')),
            pf.RawBlock(r'\fi', format='latex'),
        ]
        doc.content.extend(blocks)

        with self.subTest('handle ifttm'):
            elem = doc.content[0]
            ret = filter_action.filter(elem, elem.doc)
            self.assertEqual(ret, [])

        with self.subTest('handle para foo'):
            elem = doc.content[1]
            ret = filter_action.filter(elem, elem.doc)
            self.assertEqual(ret, [])

        with self.subTest('handle fi'):
            elem = doc.content[2]
            ret = filter_action.filter(elem, elem.doc)[0]
            self.assertIsInstance(ret, pf.Para)
            self.assertIsInstance(ret.content[0], pf.Str)
            self.assertEqual(ret.content[0].text, 'foo')

    def test_ifttm_inline_if_else_fi(self):
        """filter() should handle inline if/else/fi"""
        filter_action = IfttmFilterAction()
        doc = pf.Doc()
        blocks = [
            pf.Para(
                pf.RawInline(r'\ifttm', format='latex'),
                pf.Str('foo'),
                pf.RawInline(r'\else', format='latex'),
                pf.Str('bar'),
                pf.RawInline(r'\fi', format='latex'),
            )
        ]
        doc.content.extend(blocks)
        para = doc.content[0]

        with self.subTest('handle ifttm'):
            elem = para.content[0]
            ret = filter_action.filter(elem, elem.doc)
            self.assertEqual(ret, [])

        with self.subTest("handle Str('foo')"):
            elem = para.content[1]
            ret = filter_action.filter(elem, elem.doc)
            self.assertEqual(ret, [])

        with self.subTest('handle else'):
            elem = para.content[2]
            ret = filter_action.filter(elem, elem.doc)
            self.assertEqual(ret, [])

        with self.subTest("handle Str('bar')"):
            elem = para.content[3]
            ret = filter_action.filter(elem, elem.doc)
            self.assertEqual(ret, [])

        with self.subTest('handle fi'):
            elem = para.content[4]
            ret = filter_action.filter(elem, elem.doc)[0]
            self.assertIsInstance(ret, pf.Str)
            self.assertEqual(ret.text, 'foo')

    def test_invalid_value_elem(self):
        """filter() raises ValueError if elem=None"""
        filter_action = IfttmFilterAction()
        with self.assertRaises(ValueError):
            filter_action.filter(None, pf.Doc())

    def test_invalid_value_doc(self):
        """filter() raises ValueError if doc=None"""
        filter_action = IfttmFilterAction()
        with self.assertRaises(ValueError):
            filter_action.filter(pf.Para(), None)

    def test_str_untouched(self):
        """filter() should not change pf.Str"""
        filter_action = IfttmFilterAction()
        doc = pf.Doc()
        elem = pf.Str('foo')
        blocks = [pf.Para(elem)]
        doc.content.extend(blocks)
        ret = filter_action.filter(str, pf.Doc())
        self.assertIsNone(ret)
