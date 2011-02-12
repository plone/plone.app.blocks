from zope.interface import implements, alsoProvides, Interface

from zope import schema

from plone.app.blocks.interfaces import IOmittedField
from plone.app.blocks.interfaces import ILayoutField

from plone.app.blocks.interfaces import _

class LayoutField(schema.Text):
    """A field used to store layout information
    """
    
    implements(ILayoutField)

class ILayoutAware(Interface):
    """Behavior interface to make a type support layout.
    """
    content = LayoutField(
            title=_(u"Content"),
            description=_(u"Content of the object"),
            required=False,
        )
    
    pageSiteLayout = schema.Choice(
            title=_(u"Section layout"),
            description=_(u"Current site layout"),
            vocabulary="plone.availableSiteLayouts",
            required=False,
        )
    
    sectionSiteLayout = schema.Choice(
            title=_(u"Section layout"),
            description=_(u"Default site layout for pages in this section"),
            vocabulary="plone.availableSiteLayouts",
            required=False,
        )
    
alsoProvides(ILayoutAware['content'], IOmittedField)
alsoProvides(ILayoutAware['pageSiteLayout'], IOmittedField)
alsoProvides(ILayoutAware['sectionSiteLayout'], IOmittedField)
