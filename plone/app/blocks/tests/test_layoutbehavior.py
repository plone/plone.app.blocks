# -*- coding: utf-8 -*-
from plone.app.blocks.testing import BLOCKS_FUNCTIONAL_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import IUUID
from zope.component import getGlobalSiteManager
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

        setRoles(self.portal, TEST_USER_ID, ('Manager',))
        self.portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        self.portal['f1'].invokeFactory('Document', 'd1', title=u"Document 1")
        setRoles(self.portal, TEST_USER_ID, ('Member',))

        if HAS_PLONE_APP_CONTENTTYPES:
            from plone.app.contenttypes.interfaces import IDocument
            iface = IDocument
        else:
            iface = self.portal['f1']['d1'].__class__

        from plone.app.blocks.layoutbehavior import ILayoutAware
        from plone.app.blocks.layoutbehavior import LayoutAwareBehavior

        sm = getGlobalSiteManager()
        sm.registerAdapter(LayoutAwareBehavior, [iface])
        registrations = sm.getAdapters(
            (self.portal['f1']['d1'],),
            ILayoutAware
        )
        self.assertEqual(len(list(registrations)), 1)
        self.behavior = ILayoutAware(self.portal['f1']['d1'])
        registrations = sm.getAdapters(
            (self.portal['f1']['d1'],),
            ILayoutAware
        )
        self.assertEqual(len(list(registrations)), 1)

    def test_content(self):
        from plone.app.blocks.layoutviews import ContentLayoutView
        self.behavior.customContentLayout = \
            u'<html><body><a href="{0:s}"></a></body></html>'.format(
                'resolveuid/{0:s}'.format(IUUID(self.portal['f1'])))
        rendered = ContentLayoutView(self.portal['f1']['d1'], self.request)()

        # Test that UUID is resolved by outputfilters
        self.assertNotIn(IUUID(self.portal['f1']), rendered)
        self.assertIn(self.portal['f1'].absolute_url(), rendered)
