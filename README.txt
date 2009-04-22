Introduction
============

This package implements the 'blocks' rendering model. It provides several
transform stages that hook into plone.transformchain (which in turns hooks
into repoze.zope2). It will probably only work on Plone 4+ with Zope 2.12+.

The stages are:

 plone.app.blocks.parsexml (order 8000)
    Turns the response (temporarily) into an lxml ElementTree instance.
    
 plone.app.blocks.tilepage (order 8100)
    Turns a page with a blocks rel="layout" link into a page full of tiles
    with an <?xml-stylesheet ?> PI pointing to dynamic XSLT stylesheet (see
    below).
    
 plone.app.blocks.xslt (order 8500)
    Looks for <?xml-stylesheet ?> PIs and applies XSLT stylesheets.
    
 plone.app.blocks.serializexml (order 8999)
    Turns the result back into a string. Pretty printing will be used if
    debug mode is on.

There is also a view called @@blocks-static-content which can turn a
particular page into an XSLT stylesheet for transforming the tile page into
the final result with static content. It acts as an IPublishTraverse adapter
that just gobbles up anything on the sub-path. The tilepage transform stage
will append the object's mtime and a '.xsl' suffix to the style sheet to
aid caching and file type recognition.

See http://code.google.com/p/plone-deco/wiki/blocks for more details.
