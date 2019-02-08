# -*- coding: utf-8 -*-
from plone.app.textfield import RichText
from plone.app.textfield import RichTextValue
from plone.dexterity.fti import DexterityFTI
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.layoutbehavior import ILayoutBehaviorAdaptable
from plone.app.blocks.layoutbehavior import LayoutAwareTileDataStorage
from plone.app.blocks.testing import BLOCKS_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.registry.interfaces import IRegistry
from plone.rfc822.interfaces import IPrimaryField
from plone.supermodel.model import Schema
from plone.tiles.interfaces import ITileType
from plone.tiles.type import TileType
from plone.uuid.interfaces import IUUID
from zope.component import getUtility
from zope.component import provideUtility
from zope.interface import alsoProvides

import pkg_resources
import unittest

try:
    pkg_resources.get_distribution('plone.app.contenttypes')
except pkg_resources.DistributionNotFound:
    HAS_PLONE_APP_CONTENTTYPES = False
else:
    HAS_PLONE_APP_CONTENTTYPES = True


class TestLayoutBehavior(unittest.TestCase):

    layer = BLOCKS_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.registry = getUtility(IRegistry)
        self.maxDiff = None

        fti = DexterityFTI(
            'MyDocument',
            global_allow=True,
            behaviors=(
                'plone.app.dexterity.behaviors.metadata.IBasic',
                'plone.app.blocks.layoutbehavior.ILayoutAware'
            )
        )
        self.portal.portal_types._setObject('MyDocument', fti)

        setRoles(self.portal, TEST_USER_ID, ('Manager',))
        self.portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        self.portal['f1'].invokeFactory('MyDocument', 'd1',
                                        title=u"Document 1")
        setRoles(self.portal, TEST_USER_ID, ('Member',))

        self.behavior = ILayoutAware(self.portal['f1']['d1'])
        self.assertTrue(
            ILayoutBehaviorAdaptable.providedBy(self.behavior.context))

    def test_custom_content_layout(self):
        from plone.app.blocks.layoutviews import ContentLayoutView
        self.behavior.customContentLayout = \
            u'<html><body><a href="{0:s}"></a></body></html>'.format(
                'resolveuid/{0:s}'.format(IUUID(self.portal['f1'])))
        rendered = ContentLayoutView(self.portal['f1']['d1'], self.request)()

        # Test that UUID is resolved by outputfilters
        self.assertNotIn(IUUID(self.portal['f1']), rendered)
        self.assertIn(self.portal['f1'].absolute_url(), rendered)

    def test_content(self):
        tile = 'plone.app.tiles.demo.transient/demo'
        self.behavior.content = u"""\
<html>
<body>
<div data-tile="@@plone.app.tiles.demo.transient/demo"
data-tiledata='{"message": "Hello World!"}' />
</body>
</html>
"""
        view = self.portal['f1']['d1'].restrictedTraverse(tile)()
        self.assertEqual(
            view,
            '<html><body><b>Transient tile Hello World!</b></body></html>'
        )

        storage = LayoutAwareTileDataStorage(self.portal['f1']['d1'],
                                             self.layer['request'])
        self.assertEqual(len(storage), 1)
        self.assertEqual(list(storage), [tile])
        self.assertEqual(storage[tile]['message'], u"Hello World!")

        data = storage[tile]
        data['message'] = u"Foo bar!"
        storage[tile] = data

        delattr(self.layer['request'], '__annotations__')  # purge memoize

        view = self.portal['f1']['d1'].restrictedTraverse(tile)()
        self.assertEqual(
            view,
            '<html><body><b>Transient tile Foo bar!</b></body></html>'
        )

    def test_content_richtext(self):

        class IRichTextTile(Schema):
            html = RichText()

        alsoProvides(IRichTextTile['html'], IPrimaryField)

        provideUtility(TileType(
            name='plone.app.blocks.richtext',
            title='plone.app.blocks.richtext',
            add_permission='cmf.ModifyPortalContent',
            view_permission='zope2.View',
            schema=IRichTextTile
        ),
            provides=ITileType,
            name='plone.app.blocks.richtext')

        self.behavior.content = u"""\
<html>
<body>
<div data-tile="@@plone.app.blocks.richtext/demo"
data-tiledata='{"content-type": "text/html"}'>
<div><p>Hello World!</p></div>
</div>
</body>
</html>
"""
        storage = LayoutAwareTileDataStorage(self.portal['f1']['d1'],
                                             self.layer['request'])
        data = storage['@@plone.app.blocks.richtext/demo']

        self.assertIn('html', data)
        self.assertIsInstance(data['html'], RichTextValue)
        self.assertEqual(data['html'].output,
                         u'<p>Hello World!</p>')

        storage['@@plone.app.blocks.richtext/demo'] = {
            'html': RichTextValue(
                '<p>Foo bar!</p>',
                mimeType='text/html',
                outputMimeType='text/x-html-safe',
                encoding='utf-8'
            )
        }

        output = str(storage.storage).replace(u'\n', u'')
        self.assertIn('"html-content-type": "text/html"', output)
        self.assertIn('"html-output-content-type": "text/x-html-safe"', output)
        self.assertIn('<p>Foo bar!</p>', output)
