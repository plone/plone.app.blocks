import unittest2 as unittest

from plone.app.blocks.testing import BLOCKS_FUNCTIONAL_TESTING

class TestSiteLayout(unittest.TestCase):

    layer = BLOCKS_FUNCTIONAL_TESTING
    
    def test_default_site_layout_no_registry_key(self):
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from plone.registry.interfaces import IRegistry
        from plone.memoize.volatile import ATTR
        from zExceptions import NotFound
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        # Clear cache if there
        if hasattr(portal, ATTR):
            delattr(portal, ATTR)
        
        registry = getUtility(IRegistry)
        registry['plone.defaultSiteLayout'] = None
        
        view = getMultiAdapter((portal, request,), name=u'default-site-layout')
        self.assertRaises(NotFound, view)
    
    def test_default_site_layout(self):
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from plone.registry.interfaces import IRegistry
        from plone.memoize.volatile import ATTR
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        # Clear cache if there
        if hasattr(portal, ATTR):
            delattr(portal, ATTR)
        
        registry = getUtility(IRegistry)
        registry['plone.defaultSiteLayout'] = '/++sitelayout++testlayout1/site.html'
        
        view = getMultiAdapter((portal, request,), name=u'default-site-layout')
        rendered = view()
        
        self.assertTrue(u"Layout title" in rendered)
    
    def test_default_site_layout_cache(self):
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from plone.registry.interfaces import IRegistry
        from plone.memoize.volatile import ATTR
        from Products.CMFPlone.utils import getToolByName
        from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
        from StringIO import StringIO
        from OFS.Image import File
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        # Clear cache if there
        if hasattr(portal, ATTR):
            delattr(portal, ATTR)
        
        resources = getToolByName(portal, 'portal_resources')
        resources._setOb('sitelayout', BTreeFolder2('sitelayout'))
        resources['sitelayout']._setOb('testlayout3', BTreeFolder2('testlayout3'))
        resources['sitelayout']['testlayout3']._setOb('site.html',
                File('site.html', 'site.html', StringIO(
                            '<html><head><title>ZODB test</title></head></html>')
                        )
            )
        
        registry = getUtility(IRegistry)
        registry['plone.defaultSiteLayout'] = '/++sitelayout++testlayout3/site.html'
        
        view = getMultiAdapter((portal, request,), name=u'default-site-layout')
        rendered = view()
        
        self.assertTrue(u"ZODB test" in rendered)
        
        resources['sitelayout']['testlayout3']._delOb('site.html')
        resources['sitelayout']['testlayout3']._setOb('site.html',
                File('site.html', 'site.html', StringIO(
                            '<html><head><title>Cache test</title></head></html>')
                        )
            )
        
        view = getMultiAdapter((portal, request,), name=u'default-site-layout')
        rendered = view()
        
        self.assertFalse(u"Cache test" in rendered) # hidden by cache
        self.assertTrue(u"ZODB test" in rendered)
    
    def test_default_site_layout_invalidate_mtime(self):
        import transaction
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from plone.registry.interfaces import IRegistry
        from plone.memoize.volatile import ATTR
        from Products.CMFPlone.utils import getToolByName
        from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
        from StringIO import StringIO
        from OFS.Image import File
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        # Clear cache if there
        if hasattr(portal, ATTR):
            delattr(portal, ATTR)
        
        resources = getToolByName(portal, 'portal_resources')
        resources._setOb('sitelayout', BTreeFolder2('sitelayout'))
        resources['sitelayout']._setOb('testlayout3', BTreeFolder2('testlayout3'))
        resources['sitelayout']['testlayout3']._setOb('site.html',
                File('site.html', 'site.html', StringIO(
                            '<html><head><title>ZODB test</title></head></html>')
                        )
            )
        
        registry = getUtility(IRegistry)
        registry['plone.defaultSiteLayout'] = '/++sitelayout++testlayout3/site.html'
        
        view = getMultiAdapter((portal, request,), name=u'default-site-layout')
        rendered = view()
        
        self.assertTrue(u"ZODB test" in rendered)
        
        resources['sitelayout']['testlayout3']._delOb('site.html')
        resources['sitelayout']['testlayout3']._setOb('site.html',
                File('site.html', 'site.html', StringIO(
                            '<html><head><title>Cache test</title></head></html>')
                        )
            )
        
        # Trigger invalidation by modifying the context and committing
        portal.title = u"New title"
        transaction.commit()
        
        view = getMultiAdapter((portal, request,), name=u'default-site-layout')
        rendered = view()
        
        self.assertTrue(u"Cache test" in rendered)
        self.assertFalse(u"ZODB test" in rendered)
    
    def test_default_site_layout_invalidate_registry_key(self):
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from plone.registry.interfaces import IRegistry
        from plone.memoize.volatile import ATTR
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        # Clear cache if there
        if hasattr(portal, ATTR):
            delattr(portal, ATTR)
        
        registry = getUtility(IRegistry)
        registry['plone.defaultSiteLayout'] = '/++sitelayout++testlayout1/site.html'
        
        view = getMultiAdapter((portal, request,), name=u'default-site-layout')
        rendered = view()
        
        self.assertTrue(u"Layout title" in rendered)
        
        # Trigger invalidation by modifying the global site layout selection
        registry['plone.defaultSiteLayout'] = '/++sitelayout++testlayout2/mylayout.html'
        
        view = getMultiAdapter((portal, request,), name=u'default-site-layout')
        rendered = view()
        
        self.assertTrue(u"Layout 2 title" in rendered)
        self.assertFalse(u"Layout title" in rendered)
