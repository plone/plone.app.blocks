# -*- coding: utf-8 -*-
from plone.app.blocks.utils import resolve

import unittest


class TestUtils(unittest.TestCase):

    def test_resolve_utf8_unicode(self):
        content_layout = u"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html data-layout="./@@default-site-layout">
  <body>
    <h1>Ä</h1>
  </body>
</html>"""
        text = resolve('', content_layout).xpath('//h1')[0].text
        self.assertEqual(u'Ä', text)

    def test_resolve_utf8_bytestring(self):
        """Test fix for issue where layouts with non-ascii characters were
        not properly parsed resulting in double encoding
        """
        content_layout = u"""
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html data-layout="./@@default-site-layout">
  <body>
    <h1>Ä</h1>
  </body>
</html>""".encode('utf-8')
        text = resolve('', content_layout).xpath('//h1')[0].text
        self.assertEqual(u'Ä', text)
