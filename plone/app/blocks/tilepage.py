from plone.app.blocks import utils

from lxml import etree
from lxml.html import builder as E

def create_tilepage(request, tree):
    """Transform the response represented by the lxml tree `tree` for the
    given request into a tile page.
    
    Assumes panel merging has already happened.
    """
    
    # Find tiles in the merged document.
    tiles = utils.find_tiles(request, tree)
    
    # Change the merged document into a tile page (rather forcefully)

    html_node = tree.getroot()
    html_node.clear()

    # Add an <?xml-stylesheet ?> processing instruction pointing to a
    # dynamically generated XSLT that will transform the tilepage into the
    # content
    unique_xsl_name = "content"
    published = request.get('PUBLISHED', None)
    if published is not None and hasattr(published, '__parent__') and hasattr(published.__parent__, '_p_mtime'):
        unique_xsl_name = published.__parent__._p_mtime
    
    # The URL should include the modification time to make cache invalidation easier,
    # and the original query string, which will be used when the composite page is rendered
    xsl_url = "%s/@@blocks-static-content/%s.xsl?%s" % (request.getURL(), unique_xsl_name, request['QUERY_STRING'])
    
    stylesheet_declaration = etree.ProcessingInstruction('xml-stylesheet type="text/xsl" href="%s"' % xsl_url)
    html_node.addprevious(stylesheet_declaration)
    
    # Set up empty head and body tags so that we can merge
    head_node = E.HEAD()
    html_node.append(head_node)
    
    body_node = E.BODY()
    html_node.append(body_node)
    
    # Resolve each tile and place it into the tilepage body
    for tile_id, tile_href in tiles.items():
        tile_tree = utils.resolve(request, tile_href)
        if tile_tree is not None:
            tile_root = tile_tree.getroot()
            
            # merge tile head into tilepage
            tile_head = tile_root.find('head')
            if tile_head is not None:
                for tile_head_child in tile_head:
                    head_node.append(tile_head_child)
            
            # add tile body
            tile_body = tile_root.find('body')
            new_tile_node = E.DIV()
            new_tile_node.attrib['id'] = tile_id
            for tile_body_child in tile_body:
                new_tile_node.append(tile_body_child)
            
            body_node.append(new_tile_node)
    
    # Make the tile page XSLT
    request.response.setHeader('Content-Type', 'text/xml')
    return tree