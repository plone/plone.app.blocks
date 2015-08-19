# -*- coding: utf-8 -*-
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from lxml import html
from plone.app.blocks.interfaces import IBlocksTransformEnabled
from plone.app.blocks.interfaces import ILayoutField
from plone.app.blocks.interfaces import ILayoutFieldDefaultValue
from plone.app.blocks.interfaces import IOmittedField
from plone.app.blocks.interfaces import _
from plone.app.blocks.utils import bodyTileXPath
from plone.app.blocks.utils import resolveResource
from plone.app.layout.globals.interfaces import IViewView
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.browser.view import DefaultView
from plone.outputfilters import apply_filters
from plone.outputfilters.interfaces import IFilter
from repoze.xmliter.utils import getHTMLSerializer
from zExceptions import NotFound
from zope import schema
from zope.component import adapter, getMultiAdapter
from zope.component import getAdapters
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
from zope.interface import Interface
from zope.interface import alsoProvides
from zope.interface import implementer
from zope.interface import implements, provider
from zope.schema.interfaces import IContextAwareDefaultFactory
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
Could not render selected layout
</div>
</body>
</html>"""


class LayoutField(schema.Text):
    """A field used to store layout information
    """

    implements(ILayoutField)


@implementer(ILayoutFieldDefaultValue)
@adapter(Interface, Interface)
def layoutFieldDefaultValue(context, request):
    return u"""\
<!DOCTYPE html>
<html lang="en" data-layout="./@@page-site-layout">
<body>
<div data-panel="content">
</div>
</body>
</html>"""


@provider(IContextAwareDefaultFactory)
def layoutFieldDefaultValueFactory(context):
    if context is None:
        context = getSite()
    request = getRequest()
    return getMultiAdapter((context, request), ILayoutFieldDefaultValue)


class ILayoutAware(model.Schema):
    """Behavior interface to make a type support layout.
    """
    if HAS_DXTEXTINDEXER:
        searchable('content')
    content = LayoutField(
        title=_(u"Custom layout"),
        description=_(u"Custom content and content layout of this page"),
        defaultFactory=layoutFieldDefaultValueFactory,
        required=False
    )

    staticLayout = schema.ASCIILine(
        title=_(u'Static Layout'),
        description=_(u'Selected static layout. If selected, content is ignored.'),
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
             fields=('content', 'pageSiteLayout', 'sectionSiteLayout', 'staticLayout'))

alsoProvides(ILayoutAware, IFormFieldProvider)

alsoProvides(ILayoutAware['content'], IOmittedField)
alsoProvides(ILayoutAware['pageSiteLayout'], IOmittedField)
alsoProvides(ILayoutAware['sectionSiteLayout'], IOmittedField)


def getter(name):
    def _getter(self):
        return getattr(self.context, name)
    return _getter


def setter(name):
    def _setter(self, value):
        setattr(self.context, name, value)
    return _setter


def getSafeHTMLSerializer(data):
    """Return HTML serializer for given html"""
    # Parse layout
    if isinstance(data, unicode):
        serializer = getHTMLSerializer([data.encode('utf-8')], encoding='utf-8')
    else:
        serializer = getHTMLSerializer([data], encoding='utf-8')

    # Fix XHTML layouts with inline js (etree.tostring breaks all <![CDATA[)
    if '<![CDATA[' in data:
        serializer.serializer = html.tostring

    return serializer


def mergeContentIntoStaticLayout(content, static):
    content = getSafeHTMLSerializer(content)
    static = getSafeHTMLSerializer(static)

    contentTiles = dict(
        (node.attrib['data-tile'], node)
        for node in bodyTileXPath(content.tree)
    )

    staticTiles = dict(
        (node.attrib['data-tile'], node)
        for node in bodyTileXPath(static.tree)
    )

    # TODO: replace static tiles with matching ID content
    # TODO: search all text-tiles and replace them in order from content to static

    return ''.join(static)


@implementer(ILayoutAware)
@adapter(Interface)
class LayoutAwareAdapter(object):
    def __init__(self, context):
        self.context = context

    def get_content(self):
        # Is allowed to raise AttributeError for non-initialized value
        try:
            static = resolveResource(self.context.staticLayout)
            return mergeContentIntoStaticLayout(self.context.content, static)
        except NotFound:
            return self.context.content
        except AttributeError:
            return self.context.content

    content = property(get_content, setter('content'))
    staticLayout = property(getter('staticLayout'), setter('staticLayout'))
    pageSiteLayout = property(getter('pageSiteLayout'), setter('pageSiteLayout'))  # noqa
    contentSiteLayout = property(getter('contentSiteLayout'), setter('contentSiteLayout'))  # noqa


class SiteLayoutView(BrowserView):
    """Default site layout view called from the site layout resolving view"""

    implements(IViewView)

    index = ViewPageTemplateFile(os.path.join('templates',
                                              'main_template.pt'))

    def __call__(self):
        self.__name__ = 'main_template'
        return self.index()


class ContentLayoutView(DefaultView):
    """Default view for a layout aware page
    """

    implements(IBlocksTransformEnabled)

    def __init__(self, context, request):
        super(ContentLayoutView, self).__init__(context, request)

    def __call__(self):
        """Render the contents of the "content" field coming from
        the ILayoutAware behavior.

        This result is supposed to be transformed by plone.app.blocks.
        """
        layout = ILayoutAware(self.context).content
        # Here we skip legacy portal_transforms and call plone.outputfilters
        # directly by purpose
        filters = [f for _, f
                   in getAdapters((self.context, self.request), IFilter)]
        return apply_filters(filters, layout)
