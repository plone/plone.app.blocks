# -*- coding: utf-8 -*-
from plone.dexterity.fti import DexterityFTI
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.layoutbehavior import ILayoutBehaviorAdaptable
from plone.app.blocks.layoutbehavior import LayoutAwareTileDataStorage
from plone.app.blocks.testing import BLOCKS_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from zope.component import getUtility

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
