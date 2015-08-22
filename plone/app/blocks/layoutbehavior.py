# -*- coding: utf-8 -*-
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from lxml import html
from plone.app.blocks.interfaces import IBlocksTransformEnabled
from plone.app.blocks.interfaces import ILayoutField
from plone.app.blocks.interfaces import IOmittedField
from plone.app.blocks.interfaces import _
from plone.app.layout.globals.interfaces import IViewView
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.browser.view import DefaultView
from plone.outputfilters import apply_filters
from plone.outputfilters.interfaces import IFilter
from plone.registry.interfaces import IRegistry
from zExceptions import NotFound
from zope import schema
from zope.component import getAdapters
from zope.component import getUtility
from zope.interface import alsoProvides
from zope.interface import implements
import logging
import os

try:
    from plone.supermodel import model
    from plone.supermodel.directives import fieldset
except ImportError:
    # BBB: Plone 4.2 with Dexterity 1.x
    from plone.directives import form as model
    from plone.directives.form import fieldset

try:
    from collective.dexteritytextindexer import searchable
    HAS_DXTEXTINDEXER = True
except ImportError:
    HAS_DXTEXTINDEXER = False


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
    if HAS_DXTEXTINDEXER:
        searchable('content')
    content = LayoutField(
        title=_(u"Custom layout"),
        description=_(u"Custom content and content layout of this page"),
        default=None,
        required=False
    )

    contentLayout = schema.ASCIILine(
        title=_(u'Content Layout'),
        description=_(u'Selected content layout. If selected, custom layout is ignored.'),
        required=False)

    pageSiteLayout = schema.Choice(
        title=_(u"Site layout"),
        description=_(u"Site layout to apply to this page "
                      u"instead of the default site layout"),
        vocabulary="plone.availableSiteLayouts",
        required=False
    )

    sectionSiteLayout = schema.Choice(
        title=_(u"Section site layout"),
        description=_(u"Site layout to apply to sub-pages of this page "
                      u"instead of the default site layout"),
        vocabulary="plone.availableSiteLayouts",
        required=False
    )

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

    def __call__(self):
        self.__name__ = 'main_template'
        return self.index()


def resolveContentLayout(path):
    """Resolve given path as content layout and return the layout.

    Append X-Tile-Persistent for layout's tile URLs to allow context specific
    tile configuration overrides.
    """
    from plone.app.blocks.utils import resolve
    from plone.app.blocks.utils import tileAttrib
    from plone.app.blocks.utils import bodyTileXPath
    layout = resolve(path)
    for node in bodyTileXPath(layout):
        url = node.attrib[tileAttrib]
        if 'X-Tile-Persistent' not in url:
            if '?' in url:
                url += '&X-Tile-Persistent=yes'
            else:
                url += '?X-Tile-Persistent=yes'
        node.attrib[tileAttrib] = url
    return html.tostring(layout)


class ContentLayoutView(DefaultView):
    """Default view for a layout aware page
    """

    implements(IBlocksTransformEnabled)

    def __call__(self):
        """Render the contents of the "content" field coming from
        the ILayoutAware behavior.

        This result is supposed to be transformed by plone.app.blocks.
        """
        behavior_data = ILayoutAware(self.context)
        if behavior_data.contentLayout:
            try:
                layout = resolveContentLayout(behavior_data.contentLayout)
            except (NotFound, RuntimeError):
                layout = ''
        else:
            layout = behavior_data.content

        if not layout:
            registry = getUtility(IRegistry)
            try:
                layout_name = registry['plone.app.blocks.default_layout.%s' % self.context.portal_type]  # noqa
                layout = resolveContentLayout(layout_name)
            except (KeyError, AttributeError, NotFound, RuntimeError):
                pass

        if not layout:
            layout = ERROR_LAYOUT

        # Here we skip legacy portal_transforms and call plone.outputfilters
        # directly by purpose
        filters = [f for _, f
                   in getAdapters((self.context, self.request), IFilter)]
        return apply_filters(filters, layout)
