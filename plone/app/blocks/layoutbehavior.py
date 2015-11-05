# -*- coding: utf-8 -*-
import logging
import os

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.blocks.interfaces import IBlocksTransformEnabled
from plone.app.blocks.interfaces import ILayoutField
from plone.app.blocks.interfaces import IOmittedField
from plone.app.blocks.interfaces import _
from plone.app.layout.globals.interfaces import IViewView
from plone.autoform.directives import write_permission
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.browser.view import DefaultView
from plone.outputfilters import apply_filters
from plone.outputfilters.interfaces import IFilter
from zope import schema
from zope.component import getAdapters
from zope.interface import alsoProvides
from zope.interface import implements

try:
    from plone.supermodel import model
    from plone.supermodel.directives import fieldset
except ImportError:
    # BBB: Plone 4.2 with Dexterity 1.x
    from plone.directives import form as model
    from plone.directives.form import fieldset


logger = logging.getLogger('plone.app.blocks')


ERROR_LAYOUT = u"""
<!DOCTYPE html>
<html lang="en" data-layout="./@@page-site-layout">
<body>
<div data-panel="content">
Could not find layout for content
</div>
</body>
</html>"""


class LayoutField(schema.Text):
    """A field used to store layout information
    """

    implements(ILayoutField)


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
            u'Selected content layout. If selected, custom layout is ignored.'),
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

    fieldset('layout', label=_('Layout'),
             fields=('content', 'pageSiteLayout', 'sectionSiteLayout', 'contentLayout'))

alsoProvides(ILayoutAware, IFormFieldProvider)

alsoProvides(ILayoutAware['content'], IOmittedField)
alsoProvides(ILayoutAware['pageSiteLayout'], IOmittedField)
alsoProvides(ILayoutAware['sectionSiteLayout'], IOmittedField)


class SiteLayoutView(BrowserView):
    """Default site layout view called from the site layout resolving view"""

    implements(IViewView)

    index = ViewPageTemplateFile(os.path.join('templates',
                                              'main_template.pt'))

    def __init__(self, context, request, name='layout'):
        super(SiteLayoutView, self).__init__(context, request)
        self.__name__ = name

    def __call__(self):
        return self.index()


class ContentLayoutView(DefaultView):
    """Default view for a layout aware page
    """

    implements(IBlocksTransformEnabled)

    def __call__(self):
        """Render the contents of the "content" field coming from
        the ILayoutAware behavior.

        This result is supposed to be transformed by plone.app.blocks.
        """
        from plone.app.blocks.utils import getLayout
        layout = getLayout(self.context)

        if not layout:
            layout = ERROR_LAYOUT

        # Here we skip legacy portal_transforms and call plone.outputfilters
        # directly by purpose
        filters = [f for _, f
                   in getAdapters((self.context, self.request), IFilter)]
        return apply_filters(filters, layout)