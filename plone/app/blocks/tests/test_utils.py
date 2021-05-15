# -*- coding: utf-8 -*-
from plone.app.blocks.testing import BLOCKS_FUNCTIONAL_TESTING
from plone.app.blocks.utils import resolve
from plone.app.blocks.utils import resolveResource

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
        text = resolve("", content_layout).xpath("//h1")[0].text
        self.assertEqual(u"Ä", text)

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
</html>""".encode(
            "utf-8"
        )
        text = resolve("", content_layout).xpath("//h1")[0].text
        self.assertEqual(u"Ä", text)


class TestUtilsFunctional(unittest.TestCase):

    layer = BLOCKS_FUNCTIONAL_TESTING

    def test_resolve_resource(self):
        layout = resolveResource("/++sitelayout++testlayout1/site.html")
        self.assertIn(u"Layout panel 1", layout)

    def test_resolve_resource_with_query(self):
        layout = resolveResource("/++sitelayout++testlayout1/site.html?ajax_load=1")
        self.assertIn(u"Layout panel 1", layout)

    def test_resolve_resource_with_html_content(self):
        # make sure we can handle content containing other ++ urls
        layout = resolveResource(
            "/?content=%3Cp%3ELorem%20ipsum%20dolor%20sit%20amet,%20consectetuer%20adipiscing%20elit.%20Sed%20posuere%20interdum%20sem.%20Quisque%20ligula%20eros%20ullamcorper%20quis,%20lacinia%20quis%20facilisis%20sed%20sapien.%3C/p%3E%0A%3Cscript%20type=%22application/javascript%22%20id=%22protect-script%22%20src=%22../../../++resource++protect.js"
        )
        self.assertIn(u"Plone Open Source CMS", layout)
