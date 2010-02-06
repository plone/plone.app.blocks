from zope.component import queryUtility
from plone.registry.interfaces import IRegistry

from plone.app.blocks.interfaces import IBlocksSettings
from plone.app.blocks import utils

from lxml import etree
from lxml.html import builder as E

def createTilePage(request, tree):
    """Transform the response represented by the lxml tree `tree` for the
    given request into a tile page.
    
    Assumes panel merging has already happened.
    """
    
    renderView = None
    renderedRequestKey = None
    
    # Optionally enable ESI rendering
    registry = queryUtility(IRegistry)
    if registry is not None:
        if registry.forInterface(IBlocksSettings).esi:
            renderView = 'plone.app.blocks.esirenderer'
            renderedRequestKey = 'plone.app.blocks.esi'
    
    # Find tiles in the merged document.
    tiles = utils.findTiles(request, tree)
    
    # Change the merged document into a tile page (rather forcefully)

    htmlNode = tree.getroot()
    htmlNode.clear()

    # Add an <?xml-stylesheet ?> processing instruction pointing to a
    # dynamically generated XSLT that will transform the tilepage into the
    # content
    uniqueXSLName = "content"
    published = request.get('PUBLISHED', None)
    if published is not None and hasattr(published, '__parent__') and hasattr(published.__parent__, '_p_mtime'):
        uniqueXSLName = published.__parent__._p_mtime
    
    # The URL should include the modification time to make cache invalidation easier,
    # and the original query string, which will be used when the composite page is rendered
    xslURL = "%s/@@blocks-static-content/%s.xsl?%s" % (request.getURL(), uniqueXSLName, request['QUERY_STRING'])
    
    stylesheetDeclaration = etree.ProcessingInstruction('xml-stylesheet type="text/xsl" href="%s"' % xslURL)
    htmlNode.addprevious(stylesheetDeclaration)
    
    # Set up empty head and body tags so that we can merge
    headNode = E.HEAD()
    htmlNode.append(headNode)
    
    bodyNode = E.BODY()
    htmlNode.append(bodyNode)
    
    # Resolve each tile and place it into the tilepage body
    for tileId, tileHref in tiles.items():
        tileTree = utils.resolve(request, tileHref, renderView, renderedRequestKey)
        if tileTree is not None:
            tileRoot = tileTree.getroot()
            
            # merge tile head into tilepage
            tileHead = tileRoot.find('head')
            if tileHead is not None:
                for tileHeadChild in tileHead:
                    headNode.append(tileHeadChild)
            
            # add tile body
            tileBody = tileRoot.find('body')
            
            newTileNode = E.DIV()
            newTileNode.attrib['id'] = tileId
            
            if tileBody is not None:
                newTileNode.text = tileBody.text
                for tileBodyChild in tileBody:
                    newTileNode.append(tileBodyChild)
            
            bodyNode.append(newTileNode)
    
    # Make the tile page XSLT
    request.response.setHeader('Content-Type', 'text/xml')
    return tree
