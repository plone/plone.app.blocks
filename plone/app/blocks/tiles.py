# -*- coding: utf-8 -*-
from AccessControl import Unauthorized
from AccessControl.SecurityManagement import getSecurityManager
from lxml import etree
from lxml import html
from plone import api
from plone.app.blocks import formparser
from plone.app.blocks import utils
from plone.app.blocks.interfaces import IBlocksSettings
from plone.registry.interfaces import IRegistry
from plone.tiles.interfaces import ESI_HEADER
from plone.tiles.interfaces import ESI_HEADER_KEY
from urllib import unquote
from urlparse import urljoin
from zExceptions import NotFound
from zope.component import ComponentLookupError
from zope.component import getMultiAdapter
from zope.component import queryUtility

import logging


logger = logging.getLogger('plone.app.blocks')


def _modRequest(request, query_string):
    env = request.environ.copy()
    env['QUERY_STRING'] = query_string
    try:
        data = formparser.parse(env)
        request.tile_data = data
        if data.get('X-Tile-Persistent'):
            request.tile_persistent = True
    except:
        logger.error('Could not parse query string', exc_info=True)


def _restoreRequest(request):
    if hasattr(request, 'tile_data'):
        del request.tile_data
    if hasattr(request, 'tile_persistent'):
        del request.tile_persistent


ERROR_TILE_RESULT = """<html><body>
<p class="tileerror">
We apologize, there was an error rendering this snippet
</p></body></html>"""


UNAUTHORIZED_TILE_RESULT = """<html><body>
<p class="tileerror unauthorized">
We apologize, there was an error rendering this snippet
</p></body></html>"""


def _renderTile(request, node, contexts, baseURL, siteUrl, site, sm):
    theme_disabled = request.response.getHeader('X-Theme-Disabled')
    tileHref = node.attrib[utils.tileAttrib]
    tileTree = None
    tileData = ''
    if not tileHref.startswith('/'):
        tileHref = urljoin(baseURL, tileHref)
    try:
        # first try to resolve manually, this will be much faster than
        # doing the subrequest
        relHref = tileHref[len(siteUrl) + 1:]

        contextPath, tilePart = relHref.split('@@', 1)
        contextPath = unquote(contextPath.strip('/'))
        if contextPath not in contexts:
            ob = site.unrestrictedTraverse(contextPath)
            if not sm.checkPermission('View', ob):
                # manually check perms. We do not want restriction
                # on traversing through an object
                raise Unauthorized()
            contexts[contextPath] = ob
        context = contexts[contextPath]
        if '?' in tilePart:
            tileName, tileData = tilePart.split('?', 1)
            _modRequest(request, tileData)
        else:
            tileName = tilePart
        tileName, _, tileId = tileName.partition('/')

        tile = getMultiAdapter((context, request), name=tileName)
        try:
            if (contextPath and len(tile.__ac_permissions__) > 0 and
                    not sm.checkPermission(tile.__ac_permissions__[0][0], tile)):
                logger.info('Do not have permission for tile %s on context %s' % (
                    tileName, contextPath))
                return
            else:
                pass
        except:
            logger.warn('Could not check permissions of tile %s on context %s' % (
                tileName, contextPath),
                exc_info=True)
            return
        if tileId:
            tile.id = tileId
        try:
            res = tile()
        except:
            # error rendering, let's just cut out...
            logger.error(
                'nasty uncaught tile error, data: %s,\n%s' % (
                    tileHref,
                    repr(tileData)),
                exc_info=True)
            res = ERROR_TILE_RESULT

        if not res:
            return

        tileTree = html.fromstring(res).getroottree()
    except (ComponentLookupError, ValueError):
        # fallback to subrequest route, slower but safer?
        try:
            tileTree = utils.resolve(tileHref)
        except NotFound:
            return
        except (RuntimeError, etree.XMLSyntaxError, AttributeError):
            logger.info('error parsing tile url %s' % tileHref, exc_info=True)
            return
    except (NotFound, RuntimeError, KeyError):
        logger.info('error parsing tile url %s' % tileHref, exc_info=True)
        return
    except Unauthorized:
        logger.error(
            'unauthorized tile error, data: %s,\n%s' % (
                tileHref,
                repr(tileData)), exc_info=True)
        tileTree = html.fromstring(UNAUTHORIZED_TILE_RESULT).getroottree()
    finally:
        _restoreRequest(request)
        if theme_disabled:
            request.response.setHeader('X-Theme-Disabled', '1')
        else:
            request.response.setHeader('X-Theme-Disabled', '')

    return tileTree


def renderTiles(request, tree, baseURL=None):
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
    if baseURL is None:
        baseURL = request.getURL()
        if request.getVirtualRoot():
            # plone.subrequest deals with VHM requests
            baseURL = ''

    # optimizations...
    contexts = {}
    site = api.portal.get()
    siteUrl = site.absolute_url()
    sm = getSecurityManager()

    for tileNode in utils.headTileXPath(tree):
        tileTree = _renderTile(request, tileNode, contexts, baseURL, siteUrl, site, sm)
        if tileTree is not None:
            tileRoot = tileTree.getroot()
            content = tileRoot.find('head') or tileRoot.find('body')
            utils.replace_with_children(tileNode, content)
        else:
            parent = tileNode.getparent()
            parent.remove(tileNode)

    import pdb; pdb.set_trace()
    for tileNode in utils.bodyTileXPath(tree):
        tileTree = _renderTile(request, tileNode, contexts, baseURL, siteUrl, site, sm)
        if tileTree is not None:
            tileRoot = tileTree.getroot()

            tileHead = tileRoot.find('head')
            tileBody = tileRoot.find('body')

            if tileHead is None and tileBody is None:
                tileBody = tileRoot

            if tileHead is not None and headNode is not None:
                for tileHeadChild in tileHead:
                    headNode.append(tileHeadChild)
            utils.replace_with_children(tileNode, tileBody)
        else:
            parent = tileNode.getparent()
            parent.remove(tileNode)
    return tree
