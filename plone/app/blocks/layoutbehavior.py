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
            title=_(u"Page site layout"),
            description=_(u"Site layout to apply to the current page"),
            vocabulary="plone.availableSiteLayouts",
            required=False,
        )

    sectionSiteLayout = schema.Choice(
            title=_(u"Section site layout"),
            description=_(u"Site layout to apply to pages under this section"),
            vocabulary="plone.availableSiteLayouts",
            required=False,
        )

try:
    from plone.autoform.interfaces import IFormFieldProvider
    alsoProvides(ILayoutAware, IFormFieldProvider)
except ImportError:
    pass

alsoProvides(ILayoutAware['content'], IOmittedField)
alsoProvides(ILayoutAware['pageSiteLayout'], IOmittedField)
alsoProvides(ILayoutAware['sectionSiteLayout'], IOmittedField)
