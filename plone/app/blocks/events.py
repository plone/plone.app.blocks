# -*- coding: utf-8 -*-
from plone.app.blocks.interfaces import IAfterTileRenderEvent
from plone.app.blocks.interfaces import IBeforeTileRenderEvent
from zope.interface import implementer


class BaseTileRenderEvent(object):

    def __init__(self, tile_href, tile_node):
        self.tile_href = tile_href
        self.tile_node = tile_node


@implementer(IBeforeTileRenderEvent)
class BeforeTileRenderEvent(BaseTileRenderEvent):
    pass


@implementer(IAfterTileRenderEvent)
class AfterTileRenderEvent(BaseTileRenderEvent):
    pass
