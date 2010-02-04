# XXX: This module is borrowed largely from plone.app.relationfield; if
# five.intid gets a better setup story, we should remove this.

from zope.component import queryUtility

from zope.intid.interfaces import IIntIds
from five.intid.site import addUtility
from five.intid.intid import IntIds

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.interfaces import IDynamicType

try:
    import Products.LinguaPlone
    HAS_LINGUAPLONE = True
except:
    HAS_LINGUAPLONE = False

def addIntids(context):
    addUtility(context, IIntIds, IntIds, ofs_name='intids',
               findroot=False)

def registerAllContent(portal):
    
    catalog = getToolByName(portal, 'portal_catalog', None)
    if catalog is None:
        return
    
    intids = queryUtility(IIntIds)
    register = intids.register
    
    # Take advantage of paths stored in keyreferences in five.intid to optimize registration
    registered_paths = dict((ref.path,None) for ref in intids.ids if hasattr(ref, 'path'))
    
    # Count how many objects we register
    registered = 0
    existing = 0

    query = {'object_provides': IDynamicType.__identifier__}
    if HAS_LINGUAPLONE:
        query['Language'] = 'all'
    
    for brain in catalog(query):
        if brain.getPath() in registered_paths:
            existing += 1
            continue
        try:
            obj = brain.getObject()
            register(obj)
            registered += 1
        except (AttributeError, KeyError, TypeError):
            pass
    
    return registered, existing

def installDrafts(context):
    if context.readDataFile('plone.app.drafts.txt') is None:
        return
    
    intids = queryUtility(IIntIds)
    if intids is not None:
        return "Initid utility already exists"
    
    portal = context.getSite()
    addIntids(portal)
    registered, existing = registerAllContent(portal)
    
    return ("Added intid utility."
            "Assigned intids to %s content objects. %s objects "
            "already had intids." % (registered, existing,))
