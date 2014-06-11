from Products.CMFCore.utils import getToolByName
from z3c.form.interfaces import IAddForm
from z3c.form.widget import ComputedWidgetAttribute
from zExceptions import NotFound
from zope.component.hooks import getSite
from zope.interface import implements, alsoProvides, Interface

from zope import schema

from plone.app.blocks.interfaces import IOmittedField
from plone.app.blocks.interfaces import ILayoutField

from plone.app.blocks.interfaces import _

import logging
logger = logging.getLogger('plone.app.blocks')


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


def getDefaultPageLayout(adapter):
    portal_type = getattr(adapter.view, 'portal_type', None)
    if not portal_type:
        return u''

    types_tool = getToolByName(getSite(), 'portal_types')
    fti = getattr(types_tool, portal_type, None)
    if fti is None:
        return u''

    aliases = fti.getMethodAliases() or {}
    layout = aliases.get('layout')

    if layout:
        # XXX: p.a.b.utils is importing this module
        from plone.app.blocks.utils import resolveResource
        try:
            return resolveResource(layout)
        except NotFound as e:
            logger.warning('Missing layout {0:s}'.format(e))
    return u''


default_layout = ComputedWidgetAttribute(
    getDefaultPageLayout, view=IAddForm, field=ILayoutField)
