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

    # Find tiles in the merged document.
    tiles = utils.findTiles(request, tree, remove=True)

    root = tree.getroot()
    headNode = root.find('head')

    # Resolve each tile and place it into the tilepage body
    for (tileId, (tileHref, hasTarget)) in sorted(tiles.items(),
                                                  cmp=utils.tileSort):
        
        tileTree = utils.resolve(tileHref)

        if tileTree is not None:
            tileRoot = tileTree.getroot()

            tileTarget = utils.xpath1("//*[@id='%s']" % tileId, root)
            if hasTarget and tileTarget is None:
                continue

            # merge tile head into the page's head
            tileHead = tileRoot.find('head')
            if tileHead is not None:
                for tileHeadChild in tileHead:
                    headNode.append(tileHeadChild)

            # No target? Then we're done.
            if not hasTarget:
                continue

            # clear children, but keep attributes
            oldAttrib = dict(tileTarget.attrib)
            tileTarget.clear()
            tileTarget.attrib.update(oldAttrib)

            # insert tile target with tile body
            tileBody = tileRoot.find('body')
            if tileBody is not None:
                tileTarget.text = tileBody.text
                for tileBodyChild in tileBody:
                    tileTarget.append(tileBodyChild)

    return tree
