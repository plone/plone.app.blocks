from Acquisition import aq_base
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
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from plone.tiles.data import defaultTileDataStorage
from plone.tiles.interfaces import ITile
from plone.tiles.interfaces import ITileDataStorage
from plone.tiles.interfaces import ITileType
from repoze.xmliter.utils import getHTMLSerializer
from zExceptions import NotFound
from zope import schema
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.component import getUtility
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider

import json
import logging


logger = logging.getLogger("plone.app.blocks")


@implementer(ILayoutField)
class LayoutField(schema.Text):
    """A field used to store layout information"""


@provider(IFormFieldProvider)
class ILayoutAware(model.Schema):
    """Behavior interface to make a type support layout."""

    omitted("content")
    content = schema.Text(
        title=_("Tile content"),
        description=_("Transient tile configurations and data for this page"),
        default=None,
        required=False,
    )

    customContentLayout = LayoutField(
        title=_("Custom layout"),
        description=_("Custom content and content layout of this page"),
        default=None,
        required=False,
    )

    contentLayout = schema.ASCIILine(
        title=_("Content Layout"),
        description=_(
            "Selected content layout. If selected, custom layout is " "ignored."
        ),
        required=False,
    )

    pageSiteLayout = schema.Choice(
        title=_("Site layout"),
        description=_(
            "Site layout to apply to this page " "instead of the default site layout"
        ),
        vocabulary="plone.availableSiteLayouts",
        required=False,
    )
    write_permission(pageSiteLayout="plone.ManageSiteLayouts")

    sectionSiteLayout = schema.Choice(
        title=_("Section site layout"),
        description=_(
            "Site layout to apply to sub-pages of this page "
            "instead of the default site layout"
        ),
        vocabulary="plone.availableSiteLayouts",
        required=False,
    )
    write_permission(sectionSiteLayout="plone.ManageSiteLayouts")

    fieldset(
        "layout",
        label=_("Layout"),
        fields=(
            "content",
            "contentLayout",
            "customContentLayout",
            "pageSiteLayout",
            "sectionSiteLayout",
        ),
    )

    def tile_layout():
        """Returns HTML layout of tiles in 'content' storage."""

    def content_layout_path():
        """Get path of content layout resource."""

    def content_layout():
        """Returns the content HTML layout."""

    def site_layout():
        """Returns resource of the site layout."""

    def ajax_site_layout():
        """Get the path to the ajax site layout to use by default for the given
        content object.
        """


class ILayoutBehaviorAdaptable(Interface):
    """Marker Interface for ILayoutAware adaptable content"""


@implementer(ILayoutAware)
@adapter(Interface)
class LayoutAwareDefault:
    """Default layout lookup for a context w/o the behavior"""

    content = None
    contentLayout = None
    customContentLayout = None
    pageSiteLayout = None
    sectionSiteLayout = None

    def __init__(self, context):
        self.context = context
        self.registry = getUtility(IRegistry)

    def tile_layout(self):
        return ""

    def content_layout_path(self):
        """Get path of content layout resource."""
        portal_type = getattr(self.context, "portal_type", "").replace(" ", "-")
        content_layout_key = f"{DEFAULT_CONTENT_LAYOUT_REGISTRY_KEY}.{portal_type}"
        path = self.registry.get(content_layout_key, None)
        if path:
            return path
        return self.registry.get(DEFAULT_CONTENT_LAYOUT_REGISTRY_KEY, None)

    def content_layout(self):
        """Returns the content HTML layout."""
        path = self.content_layout_path()
        try:
            resolved = resolveResource(path)
            if isinstance(resolved, str):
                resolved = resolved.encode("utf-8")
            return applyTilePersistent(path, resolved)
        except (NotFound, RuntimeError, OSError):
            logger.warning(f"Problem with path: {path}")

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
                section_site_layout = layoutAware.sectionSiteLayout
                if section_site_layout:
                    return layoutAware.sectionSiteLayout
            parent = aq_parent(aq_inner(parent))

        return self.registry.get(DEFAULT_SITE_LAYOUT_REGISTRY_KEY)

    def ajax_site_layout(self):
        return self.registry.get(DEFAULT_AJAX_LAYOUT_REGISTRY_KEY)


@implementer(ILayoutAware)
@adapter(ILayoutBehaviorAdaptable)
class LayoutAwareBehavior(LayoutAwareDefault):
    @property
    def content(self):
        return getattr(aq_base(self.context), "content", None)

    @content.setter
    def content(self, value):
        self.context.content = value

    @property
    def customContentLayout(self):
        return getattr(aq_base(self.context), "customContentLayout", None)

    @customContentLayout.setter
    def customContentLayout(self, value):
        self.context.customContentLayout = value

    @property
    def contentLayout(self):
        return getattr(aq_base(self.context), "contentLayout", None)

    @contentLayout.setter
    def contentLayout(self, value):
        self.context.contentLayout = value

    @property
    def pageSiteLayout(self):
        return getattr(aq_base(self.context), "pageSiteLayout", None)

    @pageSiteLayout.setter
    def pageSiteLayout(self, value):
        self.context.pageSiteLayout = value

    @property
    def sectionSiteLayout(self):
        # Section site layout can be acquired and don't need aq_base
        return getattr(self.context, "sectionSiteLayout", None)

    @sectionSiteLayout.setter
    def sectionSiteLayout(self, value):
        self.context.sectionSiteLayout = value

    def tile_layout(self):
        return self.content or ""

    def content_layout_path(self):
        return self.contentLayout or super().content_layout_path()

    def content_layout(self):
        if self.customContentLayout and not self.contentLayout:
            return self.customContentLayout
        return super().content_layout()

    def site_layout(self):
        """Get the path to the site layout for a page.

        This is generally only appropriate for the view of this page.
        For a generic template or view getDefaultSiteLayout(context)
        """
        return self.pageSiteLayout or self.sectionSiteLayout or super().site_layout()


DATA_LAYOUT = """
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
    return defaultTileDataStorage(context, request, tile)


def invalidate_view_memoize(view, name, args, kwargs):
    """Invalidate @view.memoize for given view, function name, args and kwargs.

    See: plone/memoize/view.py
    """

    annotations = IAnnotations(view.request, None) or {}
    cache = annotations.get("plone.memoize")

    if not cache:
        return

    context = view.context
    try:
        context_id = context.getPhysicalPath()
    except AttributeError:
        context_id = id(context)

    # Note: we don't use args[0] in the cache key, since args[0] ==
    # view instance and the whole point is that we can cache different
    # requests

    key = (
        context_id,
        view.__class__.__name__,
        name,
        args[1:],
        frozenset(kwargs.items()),
    )

    return cache.pop(key, None)


@implementer(ITileDataStorage)
@adapter(ILayoutBehaviorAdaptable, Interface, ITile)
class LayoutAwareTileDataStorage:
    def __init__(self, context, request, tile=None):
        self.context = context
        self.request = request
        self.tile = tile

        # Parse layout
        data_layout = ILayoutAware(self.context).content or DATA_LAYOUT
        self.storage = getHTMLSerializer(
            [data_layout.encode("utf-8")], encoding="utf-8"
        )

    def sync(self):
        ILayoutAware(self.context).content = str(self.storage)

    def resolve(self, key):
        try:
            name, key = key.strip("@").split("/", 1)
        except ValueError:
            name = self.tile.__name__ if self.tile is not None else None
            if name is None:
                raise KeyError(key)
            key = key.strip("@")
        return (
            f"@@{name:s}/{key:s}",
            getUtility(ITileType, name=name).schema,
        )

    # IItemMapping
    @view.memoize
    def __getitem__(self, key):
        key, schema_ = self.resolve(key)
        for el in self.storage.tree.xpath(f'//*[contains(@data-tile, "{key:s}")]'):
            try:
                data = json.loads(el.get("data-tiledata") or "{}")
            except ValueError:
                if el.get("data-tiledata"):
                    logger.error(
                        (
                            "No JSON object could be decoded from "
                            'data "{:s}" for tile "{:s}".'
                        ).format(el.get("data-tiledata"), key)
                    )
                raise KeyError(key)

            # Read primary field content from el content
            if len(el) and len(el[0]):
                primary = "".join(
                    [html.tostring(x, encoding="utf-8").decode("utf-8") for x in el[0]]
                )
            elif len(el):
                primary = el[0].text
            else:
                primary = None
            if primary:
                for name in schema_:
                    if not IPrimaryField.providedBy(schema_[name]):
                        continue
                    data[name] = primary
                    # Supports supermodel-defined RichTextValue
                    keys = [
                        key_ for key_ in data.keys() if key_.startswith(f"{name:s}-")
                    ]
                    if keys:
                        data[name] = dict(
                            [("data", data[name])]
                            + [
                                (key_.split("-", 1)[-1], data.pop(key_))
                                for key_ in keys
                            ]
                        )
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
        for el in self.storage.tree.xpath(f'//*[contains(@data-tile, "{key:s}")]'):
            el.remove()

            # Purge view.memoize
            invalidate_view_memoize(self, "__getitem__", (self, key), {})
            invalidate_view_memoize(self, "__getitem__", (self, key.lstrip("@")), {})
            invalidate_view_memoize(
                self, "__getitem__", (self, key.split("/", 1)[-1]), {}
            )

            return self.sync()
        raise KeyError(key)

    def __setitem__(self, key, value):
        key, schema_ = self.resolve(key)
        data = json_compatible(value)

        # Store primary field as tile tag content
        primary = None
        for name in schema_:
            if IPrimaryField.providedBy(schema_[name]) and data.get(name):
                raw = data.pop(name) or ""
                if isinstance(raw, dict):  # Support supermodel RichTextValue
                    for key_ in [k for k in raw if k != "data"]:
                        data[f"{name:s}-{key_:s}"] = raw[key_]
                    raw = raw.get("data")
                try:
                    raw = "<div>{:s}</div>".format(raw or "")
                    primary = html.fromstring(raw)
                except (etree.ParseError, TypeError):
                    pass

        # Update existing value
        for el in self.storage.tree.xpath(f'//*[contains(@data-tile, "{key:s}")]'):
            el.clear()
            el.attrib["data-tile"] = key
            if data:
                el.attrib["data-tiledata"] = json.dumps(data)
            elif "data-tiledata" in el.attrib:
                del el.attrib["data-tiledata"]
            if primary is not None:
                el.append(primary)

            # Purge view.memoize
            invalidate_view_memoize(self, "__getitem__", (self, key), {})
            invalidate_view_memoize(self, "__getitem__", (self, key.lstrip("@")), {})
            invalidate_view_memoize(
                self, "__getitem__", (self, key.split("/", 1)[-1]), {}
            )

            return self.sync()

        # Add new value
        el = etree.Element("div")
        el.attrib["data-tile"] = key
        if data:
            el.attrib["data-tiledata"] = json.dumps(data)
        if primary is not None:
            el.append(primary)
        self.storage.tree.find("body").append(el)

        # Purge view.memoize
        invalidate_view_memoize(self, "__getitem__", (self, key), {})
        invalidate_view_memoize(self, "__getitem__", (self, key.lstrip("@")), {})
        invalidate_view_memoize(self, "__getitem__", (self, key.split("/", 1)[-1]), {})

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
        for el in self.storage.tree.xpath("//*[@data-tile]"):
            key = el.get("data-tile").strip("@")
            try:
                items.append((key, self[key]))
            except KeyError:
                continue
        return items

    def __len__(self):
        return len(self.items())
