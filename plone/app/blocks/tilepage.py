from urlparse import urljoin

from plone.app.blocks import utils
from plone.app.blocks import panel

from lxml import etree
from lxml.html import builder as E

def intercept(request, tree):
    """Transform the response represented by the lxml tree `tree` for the
    given request.
    
    If this returns None, the response is invalid and could not be
    transformed.
    """
    
    tree = panel.merge(request, tree)
    if tree is None:
        return None
    
    tiles = {} # id -> url
    
    base_url = request.getURL()
    
    # Find all tiles that exist in the page
    for tile_node in utils.tile_xpath(tree):
        
        tile_id = tile_node.get('target', None)
        tile_href = tile_node.get('href', None)
        
        if tile_id is not None and tile_href is not None:
            tile_href = urljoin(base_url, tile_href)
            
            tile_target_xpath = etree.XPath("//*[@id='%s']" % tile_id)
            tile_target_node = utils.xpath1(tile_target_xpath, tree)
            if tile_target_node is not None:
                tiles[tile_id] = tile_href
    
    # Change the merged document into a tile page rather forcefully
    
    html_node = tree.getroot()
    html_node.clear()

    unique_xsl_name = "content"
    published = request.get('PUBLISHED', None)
    if published is not None and hasattr(published, '__parent__') and hasattr(published.__parent__, '_p_mtime'):
        unique_xsl_name = published.__parent__._p_mtime
    
    xsl_url = "%s/@@blocks-static-content/%s.xsl" % (base_url, unique_xsl_name,)
    
    stylesheet_declaration = etree.ProcessingInstruction('xml-stylesheet type="text/xsl" href="%s"' % xsl_url)
    html_node.addprevious(stylesheet_declaration)
    
    head_node = E.HEAD()
    html_node.append(head_node)
    
    body_node = E.BODY()
    html_node.append(body_node)
    
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
            new_tile_node.attrib['id'] = "__blocks__%s" % tile_id
            for tile_body_child in tile_body:
                new_tile_node.append(tile_body_child)
            
            body_node.append(new_tile_node)

    return tree