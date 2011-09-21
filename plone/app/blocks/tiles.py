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
    tiles = utils.findTiles(request, tree, removeHeadLinks=True)

    root = tree.getroot()
    headNode = root.find('head')

    # Resolve each tile and place it into the tilepage body
    for tileId, tileHref, tileNode in tiles:
        
        tileTree = utils.resolve(tileHref)

        if tileTree is not None:
            tileRoot = tileTree.getroot()

            # merge tile head into the page's head
            tileHead = tileRoot.find('head')
            if tileHead is not None:
                for tileHeadChild in tileHead:
                    headNode.append(tileHeadChild)

            if tileNode is not None:

                # clear children of the tile placeholder, but keep attributes
                oldAttrib = {}
                for attribName, attribValue in tileNode.attrib.items():
                    # Remove tile metadata
                    if attribName == 'data-tile':
                        continue
                    if attribName == 'class' and 'tile-placeholder' in attribValue:
                        attribValue = " ".join([v for v in attribValue.split(" ") if v != "tile-placeholder"])
                        if attribValue != "":
                            oldAttrib[attribName] = attribValue
                    else:
                        oldAttrib[attribName] = attribValue

                tileNode.clear()
                tileNode.attrib.update(oldAttrib)

                # Remove tile-specific attributes

                # insert tile target with tile body
                tileBody = tileRoot.find('body')
                if tileBody is not None:
                    tileNode.text = tileBody.text
                    for tileBodyChild in tileBody:
                        tileNode.append(tileBodyChild)

    return tree
