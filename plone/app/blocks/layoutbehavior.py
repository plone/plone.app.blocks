# -*- coding: utf-8 -*-
from plone.app.blocks.interfaces import _
from plone.app.blocks.interfaces import ILayoutField
from plone.autoform.directives import write_permission
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from zope import schema
from zope.interface import implementer
from zope.interface import provider

import logging
import zope.deferredimport


logger = logging.getLogger('plone.app.blocks')

zope.deferredimport.deprecated(
    'Moved in own module due to avoid circular imports. '
    'Import from plone.app.blocks.layoutviews instead',
    SiteLayoutView='plone.app.blocks.layoutviews:SiteLayoutView',
    ContentLayoutView='plone.app.blocks.layoutviews:ContentLayoutView',
)


@implementer(ILayoutField)
class LayoutField(schema.Text):
    """A field used to store layout information
    """


@provider(IFormFieldProvider)
class ILayoutAware(model.Schema):
    """Behavior interface to make a type support layout.
    """
    content = LayoutField(
        title=_(u"Custom layout"),
        description=_(u"Custom content and content layout of this page"),
        default=None,
        required=False
    )

    contentLayout = schema.ASCIILine(
        title=_(u'Content Layout'),
        description=_(
            u'Selected content layout. If selected, custom layout is '
            u'ignored.'),
        required=False)

    pageSiteLayout = schema.Choice(
        title=_(u"Site layout"),
        description=_(u"Site layout to apply to this page "
                      u"instead of the default site layout"),
        vocabulary="plone.availableSiteLayouts",
        required=False
    )
    write_permission(pageSiteLayout="plone.ManageSiteLayouts")

    sectionSiteLayout = schema.Choice(
        title=_(u"Section site layout"),
        description=_(u"Site layout to apply to sub-pages of this page "
                      u"instead of the default site layout"),
        vocabulary="plone.availableSiteLayouts",
        required=False
    )
    write_permission(sectionSiteLayout="plone.ManageSiteLayouts")

    fieldset(
        'layout',
        label=_('Layout'),
        fields=(
            'content',
            'pageSiteLayout',
            'sectionSiteLayout',
            'contentLayout'
        )
    )
