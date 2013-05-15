from zExceptions import NotFound
from urlparse import urljoin

from zope.component import queryUtility

from plone.registry.interfaces import IRegistry

from plone.tiles.interfaces import ESI_HEADER, ESI_HEADER_KEY

from plone.app.blocks.interfaces import IBlocksSettings
from plone.app.blocks import utils


def renderTiles(request, tree):
    """Find all tiles in the given response, contained in the lxml element
    tree `tree`, and insert them into the ouput.

    Assumes panel merging has already happened.
    """

    # Optionally enable ESI rendering in tiles that support this
    if not request.getHeader(ESI_HEADER):
        registry = queryUtility(IRegistry)
        if registry is not None:
            if registry.forInterface(IBlocksSettings).esi:
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
        except NotFound:
            continue
        if tileTree is not None:
            tileRoot = tileTree.getroot()
            utils.replace_content(tileNode, tileRoot.find('head'))

    for tileNode in utils.bodyTileXPath(tree):
        tileHref = tileNode.attrib[utils.tileAttrib]
        if not tileHref.startswith('/'):
            tileHref = urljoin(baseURL, tileHref)
        try:
            tileTree = utils.resolve(tileHref)
        except NotFound:
            continue
        if tileTree is not None:
            tileRoot = tileTree.getroot()
            tileHead = tileRoot.find('head')
            if tileHead is not None:
                for tileHeadChild in tileHead:
                    headNode.append(tileHeadChild)
            utils.replace_content(tileNode, tileRoot.find('body'))

    return tree
