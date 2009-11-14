from plone.app.blocks import utils

def renderTiles(request, tree):
    """Find all tiles in the given response, contained in the lxml element
    tree `tree`, and insert them into the ouput.
    
    Assumes panel merging has already happened.
    """
    
    # Find tiles in the merged document.
    tiles = utils.findTiles(request, tree, remove=True)
    
    root = tree.getroot()
    head_node = root.find('head')
    
    # Resolve each tile and place it into the tilepage body
    for tile_id, tile_href in tiles.items():
        tile_tree = utils.resolve(request, tile_href)
        if tile_tree is not None:
            tile_root = tile_tree.getroot()
            
            tile_target = utils.xpath1("//*[@id='%s']" % tile_id, root)
            if tile_target is None:
                continue
            
            # merge tile head into the page's head
            tile_head = tile_root.find('head')
            if tile_head is not None:
                for tile_head_child in tile_head:
                    head_node.append(tile_head_child)
            
            # clear children, but keep attributes
            old_attrib = dict(tile_target.attrib)
            tile_target.clear()
            tile_target.attrib.update(old_attrib)
            
            # insert tile target with tile body
            tile_body = tile_root.find('body')
            for tile_body_child in tile_body:
                tile_target.append(tile_body_child)

    return tree