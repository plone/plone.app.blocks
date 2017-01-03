# -*- coding: utf-8 -*-
from lxml import html
from lxml.etree import XSLTApplyError
from plone.app.blocks import PloneMessageFactory
from plone.app.blocks import utils
from plone.app.blocks.interfaces import IBlocksSettings
from plone.app.blocks.utils import resolve_transform
from plone.registry.interfaces import IRegistry
from plone.tiles.interfaces import ESI_HEADER
from plone.tiles.interfaces import ESI_HEADER_KEY
from urlparse import urljoin
from zExceptions import NotFound
from zope.component import queryUtility
from zope.i18n import translate

import logging


logger = logging.getLogger(__name__)


def errorTile(request):
    msg = PloneMessageFactory('There was an error while rendering this tile')
    translated = translate(msg, context=request)
    return html.fromstring(translated).getroottree()


def renderTiles(request, tree):
    """Find all tiles in the given response, contained in the lxml element
    tree `tree`, and insert them into the output.

    Assumes panel merging has already happened.
    """
    # Optionally enable ESI rendering in tiles that support this
    if not request.getHeader(ESI_HEADER):
        registry = queryUtility(IRegistry)
        if registry is not None:
            if registry.forInterface(IBlocksSettings, check=False).esi:
                request.environ[ESI_HEADER_KEY] = 'true'

    root = tree.getroot()
    headNode = root.find('head')
    baseURL = request.getURL()
    if request.getVirtualRoot():
        # plone.subrequest deals with VHM requests
        baseURL = ''
    for tileNode in utils.headTileXPath(tree):
        tileHref = tileNode.attrib[utils.tileAttrib]
        if not tileHref.startswith('/'):
            tileHref = urljoin(baseURL, tileHref)
        try:
            tileTree = utils.resolve(tileHref)
        except RuntimeError:
            tileTree = None
        except NotFound:
            logger.warn(
                'NotFound while trying to render tile: {0}'.format(
                    tileHref
                )
            )
            continue
        if tileTree is not None:
            tileRoot = tileTree.getroot()
            utils.replace_with_children(tileNode, tileRoot.find('head'))

    for tileNode in utils.bodyTileXPath(tree):
        tileHref = tileNode.attrib[utils.tileAttrib]
        tileRulesHref = tileNode.attrib.get(utils.tileRulesAttrib)

        if not tileHref.startswith('/'):
            tileHref = urljoin(baseURL, tileHref)
        try:
            tileTree = utils.resolve(tileHref)
        except RuntimeError:
            tileTree = errorTile(request)
        except NotFound:
            continue

        if tileRulesHref:
            if not tileRulesHref.startswith('/'):
                tileRulesHref = urljoin(baseURL, tileRulesHref)
            try:
                tileTransform = resolve_transform(tileRulesHref, tileNode)
            except NotFound:
                tileTransform = None
            del tileNode.attrib[utils.tileRulesAttrib]
        else:
            tileTransform = None

        if tileTree is not None:
            tileRoot = tileTree.getroot()

            tileHead = tileRoot.find('head')
            tileBody = tileRoot.find('body')

            if tileHead is None and tileBody is None:
                tileBody = tileRoot

            if tileTransform is not None:
                try:
                    result = tileTransform(tileBody).getroot()
                    del tileBody[:]
                    tileBody.append(result)
                except XSLTApplyError:
                    logger.exception(
                        'Failed to transform tile {0:s} for {0:s}'.format(
                            tileHref, baseURL))
            if tileHead is not None:
                for tileHeadChild in tileHead:
                    headNode.append(tileHeadChild)
            utils.replace_with_children(tileNode, tileBody)

    return tree
