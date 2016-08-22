# -*- coding: utf-8 -*-
from lxml.html import fromstring
from plone.app.blocks import utils
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.tiles.data import ANNOTATIONS_KEY_PREFIX
from zope.annotation.interfaces import IAnnotations


def onLayoutEdited(obj, event):
    """
    need to get the layout because you need to know what are
    acceptible storage values
    """
    lookup = ILayoutAware(obj)
    layout = lookup.content_layout()

    if not layout:
        return

    tree = fromstring(layout)
    tile_keys = []
    for el in utils.bodyTileXPath(tree):
        tile_url = el.attrib.get('data-tile', '')
        if 'plone.app.standardtiles.field' in tile_url:
            continue
        tile_keys.append(
            ANNOTATIONS_KEY_PREFIX +
            '.' +
            tile_url.split('?')[0].split('/')[-1]
        )

    annotations = IAnnotations(obj)
    for key in list(annotations.keys()):
        if key.startswith(ANNOTATIONS_KEY_PREFIX) and key not in tile_keys:
            del annotations[key]
