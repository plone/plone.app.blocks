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

    settings = None
    registry = queryUtility(IRegistry)
    if registry is not None:
        settings = registry.forInterface(IBlocksSettings, False)

    # Optionally enable ESI rendering in tiles that support this
    if not request.getHeader(ESI_HEADER):
        if settings is not None and settings.esi:
            request.environ[ESI_HEADER_KEY] = 'true'

    root = tree.getroot()
    headNode = root.find('head')
    baseURL = request.getURL()

    for tileNode in utils.headTileXPath(tree):
        tileHref = urljoin(baseURL, tileNode.attrib[utils.tileAttrib])
        tileTree = utils.resolve(tileHref)
        if tileTree is not None:
            tileRoot = tileTree.getroot()
            utils.replace_with_children(tileNode, tileRoot.find('head'))

    for tileNode in utils.bodyTileXPath(tree):
        tileHref = urljoin(baseURL, tileNode.attrib[utils.tileAttrib])
        tileTree = utils.resolve(tileHref)
        if tileTree is not None:
            tileRoot = tileTree.getroot()
            tileHead = tileRoot.find('head')
            if tileHead is not None:
                for tileHeadChild in tileHead:
                    headNode.append(tileHeadChild)
            if settings is not None and settings.retain_tile_links:
                utils.replace_content(tileNode, tileRoot.find('body'))
            else:
                utils.replace_with_children(tileNode, tileRoot.find('body'))

    return tree
