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
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        # Clear cache if there
        if hasattr(portal, ATTR):
            delattr(portal, ATTR)
        
        registry = getUtility(IRegistry)
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = None
        
        view = getMultiAdapter((portal, request,), name=u'default-site-layout')
        self.assertRaises(NotFound, view)
    
    def test_default_site_layout(self):
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from plone.registry.interfaces import IRegistry
        from plone.memoize.volatile import ATTR
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        # Clear cache if there
        if hasattr(portal, ATTR):
            delattr(portal, ATTR)
        
        registry = getUtility(IRegistry)
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout1/site.html'
        
        view = getMultiAdapter((portal, request,), name=u'default-site-layout')
        rendered = view()
        
        self.assertTrue(u"Layout title" in rendered)
    
    def test_default_site_layout_section_override(self):
        from zope.interface import implements
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from zope.component import getSiteManager
        from zope.component import adapts
        from plone.registry.interfaces import IRegistry
        from plone.app.testing import setRoles
        from plone.app.testing import TEST_USER_ID
        from plone.app.blocks.layoutbehavior import ILayoutAware
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        setRoles(portal, TEST_USER_ID, ('Manager',))
        portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        portal['f1'].invokeFactory('Document', 'd1', title=u"Document 1")
        setRoles(portal, TEST_USER_ID, ('Member',))
        
        registry = getUtility(IRegistry)
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout1/site.html'
        
        class FolderLayoutAware(object):
            implements(ILayoutAware)
            adapts(portal['f1'].__class__)
            
            def __init__(self, context):
                self.context = context
            
            content = u"<html><body>N/A</body></html>"
            sectionSiteLayout = '/++sitelayout++testlayout2/mylayout.html'
            pageSiteLayout = None
        
        # Register a local adapter for easy rollback
        sm = getSiteManager()
        sm.registerAdapter(FolderLayoutAware)
        
        view = getMultiAdapter((portal['f1']['d1'], request,), name=u'default-site-layout')
        rendered = view()
        
        self.assertFalse(u"Layout title" in rendered)
        self.assertTrue(u"Layout 2 title" in rendered)
    
    def test_default_site_layout_section_no_override(self):
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from plone.registry.interfaces import IRegistry
        from plone.app.testing import setRoles
        from plone.app.testing import TEST_USER_ID
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        setRoles(portal, TEST_USER_ID, ('Manager',))
        portal.invokeFactory('Folder', 'f1', title=u"Folder 1")
        portal['f1'].invokeFactory('Document', 'd1', title=u"Document 1")
        setRoles(portal, TEST_USER_ID, ('Member',))
        
        registry = getUtility(IRegistry)
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout1/site.html'
        
        view = getMultiAdapter((portal['f1']['d1'], request,), name=u'default-site-layout')
        rendered = view()
        
        self.assertFalse(u"Layout 2 title" in rendered)
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
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        
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
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout3/site.html'
        
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
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        
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
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout3/site.html'
        
        view = getMultiAdapter((portal, request,), name=u'default-site-layout')
        rendered = view()
        
        self.assertTrue(u"ZODB test" in rendered)
        
        # Trigger invalidation by modifying the context and committing
        portal.title = u"New title"
        transaction.commit()
        
        # Modify the site layout
        resources['sitelayout']['testlayout3']._delOb('site.html')
        resources['sitelayout']['testlayout3']._setOb('site.html',
                File('site.html', 'site.html', StringIO(
                            '<html><head><title>Cache test</title></head></html>')
                        )
            )
        
        view = getMultiAdapter((portal, request,), name=u'default-site-layout')
        rendered = view()
        
        self.assertTrue(u"Cache test" in rendered)
        self.assertFalse(u"ZODB test" in rendered)
    
    def test_default_site_layout_invalidate_registry_key(self):
        from zope.component import getUtility
        from zope.component import getMultiAdapter
        from plone.registry.interfaces import IRegistry
        from plone.memoize.volatile import ATTR
        from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
        
        portal = self.layer['portal']
        request = self.layer['request']
        
        # Clear cache if there
        if hasattr(portal, ATTR):
            delattr(portal, ATTR)
        
        registry = getUtility(IRegistry)
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout1/site.html'
        
        view = getMultiAdapter((portal, request,), name=u'default-site-layout')
        rendered = view()
        
        self.assertTrue(u"Layout title" in rendered)
        
        # Trigger invalidation by modifying the global site layout selection
        registry[DEFAULT_SITE_LAYOUT_REGISTRY_KEY] = '/++sitelayout++testlayout2/mylayout.html'
        
        view = getMultiAdapter((portal, request,), name=u'default-site-layout')
        rendered = view()
        
        self.assertTrue(u"Layout 2 title" in rendered)
        self.assertFalse(u"Layout title" in rendered)
