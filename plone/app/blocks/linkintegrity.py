import re

from plone.app.blocks.layoutbehavior import ILayoutBehaviorAdaptable
from plone.app.blocks import utils
from plone.app.linkintegrity.interfaces import IRetriever
from plone.app.linkintegrity.parser import extractLinks
from plone.app.linkintegrity.retriever import DXGeneral
from plone.app.standardtiles import html
from plone.app.standardtiles import existingcontent
from plone.tiles.interfaces import ITile
from repoze.xmliter.utils import getHTMLSerializer
from zope.component import adapter
from zope.interface import implementer
try:
    # Plone 5.2+
    from Products.CMFPlone.utils import safe_bytes
except ImportError:
    # BBB for Plone 5.1
    from Products.CMFPlone.utils import safe_encode as safe_bytes


@implementer(IRetriever)
@adapter(ILayoutBehaviorAdaptable)
class BlocksDXGeneral(DXGeneral):
    """General retriever for DX that extracts URLs from (rich) text fields.
    """

    def __init__(self, context):
        self.context = context

    def retrieveLinks(self):
        """Finds all links from the object and return them.
        """
        links = super(BlocksDXGeneral, self).retrieveLinks()
        links |= self.retrieveLinksFromTiles()
        return links

    def retrieveLinksFromTiles(self):

        links = set()

        if self.context.customContentLayout is None:
            return links

        iterable = [
            re.sub(b"&#13;", b"\n", re.sub(b"&#13;\n", b"\n", safe_bytes(item)))
            for item in self.context.customContentLayout
            if item
        ]
        result = getHTMLSerializer(
            # safe_bytes (called just before) assumes 'utf-8' encoding
            # thus, we use it here as well
            # if other encoding is needed, those are two places to change
            iterable, pretty_print=False, encoding='utf-8'
        )


        for tile_node in utils.bodyTileXPath(result.tree):
            tile_url = tile_node.attrib[utils.tileAttrib]
            # assume request query parameters are always useless
            # thus ignore any chars from '?'
            tile_name = tile_url.split('?')[0]
            # eat first two characters of url ('./')
            tile_name = tile_name[2:]
            tile = self.context.restrictedTraverse(tile_name)
            links |= IRetriever(tile).retrieveLinks()

        return links


@implementer(IRetriever)
@adapter(ITile)
class TileGeneral(object):

    def __init__(self, context):
        self.context = context

    def retrieveLinks(self):
        return set()


@implementer(IRetriever)
@adapter(html.HTMLTile)
class HTMLTile(object):

    def __init__(self, context):
        self.context = context

    def retrieveLinks(self):
        content = self.context.data['content']
        # layout behavior tile storage hard codes 'utf-8' encoding
        # thus we do the same.
        links = set(extractLinks(content, 'utf-8'))
        return links


@implementer(IRetriever)
@adapter(existingcontent.ExistingContentTile)
class ExistingContentTile(object):

    def __init__(self, context):
        self.context = context

    def retrieveLinks(self):
        content_uid = self.context.data['content_uid']
        links = set(['../resolveuid/%s' % content_uid])
        return links

