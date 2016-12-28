# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from Acquisition import aq_parent
from lxml import etree
from lxml import html
from plone.app.blocks.interfaces import _
from plone.app.blocks.interfaces import DEFAULT_AJAX_LAYOUT_REGISTRY_KEY
from plone.app.blocks.interfaces import DEFAULT_CONTENT_LAYOUT_REGISTRY_KEY
from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
from plone.app.blocks.interfaces import ILayoutField
from plone.app.blocks.utils import applyTilePersistent
from plone.app.blocks.utils import resolveResource
from plone.autoform.directives import omitted
from plone.autoform.directives import write_permission
from plone.autoform.interfaces import IFormFieldProvider
from plone.jsonserializer.deserializer.converters import schema_compatible
from plone.jsonserializer.serializer.converters import json_compatible
from plone.memoize import view
from plone.registry.interfaces import IRegistry
from plone.rfc822.interfaces import IPrimaryField
from plone.supermodel.directives import fieldset
from plone.supermodel import model
from plone.tiles.data import defaultTileDataStorage
from plone.tiles.interfaces import ITile
from plone.tiles.interfaces import ITileDataStorage
from plone.tiles.interfaces import ITileType
from repoze.xmliter.utils import getHTMLSerializer
from zExceptions import NotFound
from zope.component import adapter
from zope.component import getUtility
from zope.component import queryUtility
from zope.deprecation import deprecate
from zope import schema
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider
import json
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
    omitted('content')
    content = schema.Text(
        title=_(u"Tile content"),
        description=_(u"Transient tile configurations and data for this page"),
        default=None,
        required=False
    )

    customContentLayout = LayoutField(
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
            'contentLayout',
            'customContentLayout',
            'pageSiteLayout',
            'sectionSiteLayout'
        )
    )

    def tile_layout():
        """Returns HTML layout of tiles in 'content' storage.
        """

    def content_layout_path():
        """Get path of content layout resource.
        """

    def content_layout():
        """Returns the content HTML layout.
        """

    def site_layout():
        """Returns resource of the site layout.
        """

    def ajax_site_layout():
        """Get the path to the ajax site layout to use by default for the given
        content object.
        """


class ILayoutBehaviorAdaptable(Interface):
    """Marker Interface for ILayoutAware adaptable content
    """


@implementer(ILayoutAware)
@adapter(Interface)
class LayoutAwareDefault(object):
    """Default layout lookup for a context w/o the behavior
    """

    content = None
    contentLayout = None
    customContentLayout = None
    pageSiteLayout = None
    sectionSiteLayout = None

    def __init__(self, context):
        self.context = context

    def tile_layout(self):
        return u''

    def content_layout_path(self):
        """Get path of content layout resource.
        """
        registry = getUtility(IRegistry)
        path = None
        content_layout_key = u'{0}.{1}'.format(
            DEFAULT_CONTENT_LAYOUT_REGISTRY_KEY,
            getattr(self.context, 'portal_type', '').replace(' ', '-')
        )
        path = registry.get(content_layout_key, None)
        path = path or registry.get(DEFAULT_CONTENT_LAYOUT_REGISTRY_KEY, None)
        return path

    def content_layout(self):
        """Returns the content HTML layout.
        """
        layout = None
        path = self.content_layout_path()
        try:
            resolved = resolveResource(path)
            layout = applyTilePersistent(path, resolved)
        except (NotFound, RuntimeError, IOError):
            pass
        return layout

    def site_layout(self):
        """Bubble up looking for an sectionSiteLayout, otherwise lookup the
        global sitelayout.

        Note: the sectionSiteLayout on context is for pages *under* context,
        not necessarily context itself
        """
        parent = aq_parent(aq_inner(self.context))
        while parent is not None:
            layoutAware = ILayoutAware(parent, None)
            if layoutAware is not None:
                if getattr(layoutAware, 'sectionSiteLayout', None):
                    return layoutAware.sectionSiteLayout
            parent = aq_parent(aq_inner(parent))

        registry = queryUtility(IRegistry)
        if registry is None:
            return None

        return registry.get(DEFAULT_SITE_LAYOUT_REGISTRY_KEY)

    def ajax_site_layout(self):
        registry = queryUtility(IRegistry)
        if registry is not None:
            return registry.get(DEFAULT_AJAX_LAYOUT_REGISTRY_KEY)
        else:
            return self.context.site_layout


@implementer(ILayoutAware)
@adapter(ILayoutBehaviorAdaptable)
class LayoutAwareBehavior(LayoutAwareDefault):

    @property
    def content(self):
        return getattr(self.context, 'content', None)

    @content.setter
    def content(self, value):
        self.context.content = value

    @property
    def customContentLayout(self):
        return getattr(self.context, 'customContentLayout', None)

    @customContentLayout.setter
    def customContentLayout(self, value):
        self.context.customContentLayout = value

    @property
    def contentLayout(self):
        return getattr(self.context, 'contentLayout', None)

    @contentLayout.setter
    def contentLayout(self, value):
        self.context.contentLayout = value

    @property
    def pageSiteLayout(self):
        return getattr(self.context, 'pageSiteLayout', None)

    @pageSiteLayout.setter
    def pageSiteLayout(self, value):
        self.context.pageSiteLayout = value

    @property
    def sectionSiteLayout(self):
        return getattr(self.context, 'sectionSiteLayout', None)

    @sectionSiteLayout.setter
    def sectionSiteLayout(self, value):
        self.context.sectionSiteLayout = value

    def tile_layout(self):
        return self.content or u''

    def content_layout_path(self):
        path = self.contentLayout
        return path or super(LayoutAwareBehavior, self).content_layout_path()

    def content_layout(self):
        if self.customContentLayout and not self.contentLayout:
            return self.customContentLayout
        return super(LayoutAwareBehavior, self).content_layout()

    def site_layout(self):
        """Get the path to the site layout for a page.

        This is generally only appropriate for the view of this page.
        For a generic template or view getDefaultSiteLayout(context)
        """
        return self.pageSiteLayout or \
            self.sectionSiteLayout or \
            super(LayoutAwareBehavior, self).site_layout()


DATA_LAYOUT = u"""
<!DOCTYPE html>
<html lang="en" data-layout="./@@page-site-layout">
<body data-panel="content">
</body>
</html>"""


@implementer(ITileDataStorage)
@adapter(ILayoutBehaviorAdaptable, Interface, ITile)
def layoutAwareTileDataStorage(context, request, tile):
    schema = getUtility(ITileType, name=tile.__name__).schema
    if schema and tile.id is not None:
        return LayoutAwareTileDataStorage(context, request, tile)
    else:
        return defaultTileDataStorage(context, request, tile)


@implementer(ITileDataStorage)
@adapter(ILayoutBehaviorAdaptable, Interface, ITile)
class LayoutAwareTileDataStorage(object):
    def __init__(self, context, request, tile=None):
        self.context = context
        self.request = request
        self.tile = tile

        # Parse layout
        data_layout = (ILayoutAware(self.context).content or DATA_LAYOUT)
        self.storage = getHTMLSerializer([data_layout.encode('utf-8')],
                                         pretty_print=True,
                                         encoding='utf-8')

    def sync(self):
        ILayoutAware(self.context).content = str(self.storage)

    def resolve(self, key):
        if self.tile is None:
            name = None
        else:
            name = self.tile.__name__
        try:
            name, key = key.strip('@').split('/', 1)
        except ValueError:
            if name is None:
                raise KeyError(key)
            key = key.strip('@')
        return ('@@{0:s}/{1:s}'.format(name, key),
                getUtility(ITileType, name=name).schema)

    # IItemMapping
    @view.memoize
    def __getitem__(self, key):
        key, schema_ = self.resolve(key)
        for el in self.storage.tree.xpath(
                '//*[contains(@data-tile, "{0:s}")]'.format(key)):
            try:
                data = json.loads(el.get('data-tiledata') or '{}')
            except ValueError:
                if el.get('data-tiledata'):
                    logger.error((u'No JSON object could be decoded from '
                                  u'data "{0:s}" for tile "{0:1}".').format(
                        el.get('data-tiledata'), key))
                raise KeyError(key)

            # Read primary field content from el content
            if len(el) and len(el[0]):
                primary = u''.join(
                    [html.tostring(x, encoding='utf-8').decode('utf-8')
                     for x in el[0]])
            elif len(el):
                primary = el[0].text
            else:
                primary = None
            if primary:
                for name in schema_:
                    if IPrimaryField.providedBy(schema_[name]):
                        data[name] = primary
                        break

            return schema_compatible(data, schema_)
        raise KeyError(key)

    # IReadMapping
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    # IReadMapping
    def __contains__(self, key):
        return bool(self.get(key, None))

    # IWriteMapping
    def __delitem__(self, key):
        key, schema_ = self.resolve(key)
        for el in self.storage.tree.xpath(
                '//*[contains(@data-tile, "{0:s}")]'.format(key)):
            el.remove()
            return self.sync()
        raise KeyError(key)

    def __setitem__(self, key, value):
        key, schema_ = self.resolve(key)
        data = json_compatible(value)

        # Store primary field as tile tag content
        primary = None
        for name in schema_:
            if IPrimaryField.providedBy(schema_[name]) and data.get(name):
                try:
                    raw = u'<div>{0:s}</div>'.format(data.pop(name) or u'')
                    primary = html.fromstring(raw)
                except (etree.ParseError, TypeError):
                    pass

        # Update existing value
        for el in self.storage.tree.xpath(
                '//*[contains(@data-tile, "{0:s}")]'.format(key)):
            el.clear()
            el.attrib['data-tile'] = key
            if data:
                el.attrib['data-tiledata'] = json.dumps(data)
            elif 'data-tiledata' in el.attrib:
                del el.attrib['data-tiledata']
            if primary is not None:
                el.append(primary)
            return self.sync()

        # Add new value
        el = etree.Element('div')
        el.attrib['data-tile'] = key
        if data:
            el.attrib['data-tiledata'] = json.dumps(data)
        if primary is not None:
            el.append(primary)
        self.storage.tree.find('body').append(el)
        self.sync()

    # IEnumerableMapping
    def keys(self):
        # We can only know valid keys by iterating decodeable values
        return [x[0] for x in self.items()]

    def __iter__(self):
        for item in self.items():
            yield item[0]

    def values(self):
        return [x[-1] for x in self.items()]

    def items(self):
        items = []
        for el in self.storage.tree.xpath('//*[@data-tile]'):
            key = el.get('data-tile').strip('@')
            try:
                items.append((key, self[key]))
            except KeyError:
                continue
        return items

    def __len__(self):
        return len(self.items())


@deprecate(
    'adapt with ILayoutAware instead, call adapter.site_layout()'
)
def getLayoutAwareSiteLayout(content):
    lookup = ILayoutAware(content)
    return lookup.site_layout()


@deprecate(
    'adapt with ILayoutAware instead, call adapter.content_layout()'
)
def getLayout(content):
    lookup = ILayoutAware(content)
    return lookup.content_layout()


@deprecate(
    'adapt with ILayoutAware instead. Never depend on the default. '
    'In fact this was meant only for internal use.'
)
def getDefaultSiteLayout(context):
    """Get the path to the site layout to use by default for the given content
    object
    """
    lookup = LayoutAwareDefault(context)
    return lookup.site_layout()


@deprecate(
    'adapt with ILayoutAware instead, call adapter.ajax_site_layout()'
)
def getDefaultAjaxLayout(context):
    """Get the path to the ajax site layout to use by default for the given
    content object
    """
    lookup = ILayoutAware(context)
    return lookup.ajax_site_layout()
