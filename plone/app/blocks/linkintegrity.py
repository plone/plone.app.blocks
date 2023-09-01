from plone.app.blocks import utils
from plone.app.blocks.layoutbehavior import ILayoutBehaviorAdaptable
from plone.app.linkintegrity.interfaces import IRetriever
from plone.app.linkintegrity.retriever import DXGeneral
from plone.base.utils import safe_bytes
from plone.tiles.interfaces import ITile
from repoze.xmliter.utils import getHTMLSerializer
from zope.component import adapter
from zope.interface import implementer

import re


@implementer(IRetriever)
@adapter(ILayoutBehaviorAdaptable)
class BlocksDXGeneral(DXGeneral):
    """General retriever for DX that extracts URLs from (rich) text fields."""

    def __init__(self, context):
        self.context = context

    def retrieveLinks(self):
        """Finds all links from the object and return them."""
        links = super(BlocksDXGeneral, self).retrieveLinks()
        links |= self.retrieveLinksFromTiles()
        return links

    def retrieveLinksFromTiles(self):

        links = set()

        if self.context.customContentLayout is None:
            return links

        if not hasattr(self.context, "REQUEST"):
            # context has not been added to a container yet.
            # This happens when pasting an item.
            # This easily leads to errors traversing to tiles.
            # Return the empty set for now.
            # This code will be triggered again shortly after by another event.
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
            iterable,
            pretty_print=False,
            encoding="utf-8",
        )

        for tile_node in utils.bodyTileXPath(result.tree):
            tile_url = tile_node.attrib[utils.tileAttrib]
            # assume request query parameters are always useless
            # thus ignore any chars from '?'
            tile_name = tile_url.split("?")[0]
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
