from urlparse import urlsplit

import logging

logger = logging.getLogger('plone.app.blocks')

from zope.interface import directlyProvidedBy, directlyProvides

from AccessControl import Unauthorized
from zExceptions import NotFound

try:
    from repoze.zope2.mapply import mapply, missing_name, dont_publish_class
except ImportError:
    from ZPublisher.mapply import mapply
    from ZPublisher.Publish import missing_name, dont_publish_class

from lxml import etree
from lxml import html

head_xpath   = etree.XPath("/html/head")
layout_xpath = etree.XPath("/html/head/link[@rel='layout']")
tile_xpath   = etree.XPath("/html/head/link[@rel='tile']")
panel_xpath  = etree.XPath("/html/head/link[@rel='panel']")

def clone_request(request, url):
    """Clone the given request for use in traversal to the given URL.
    
    This will set up request.form as well.
    
    The returned request should be closed with request.close()
    """
    #  normalise url and split query string

    url_parts = urlsplit(url)    
    base_url = url_parts.geturl().split('?')[0]
    
    # Clone the request so that we can traverse from it.
    
    request_clone = request.clone()
    
    # Make sure the new request provides the same markers as our old one
    directlyProvides(request_clone, *directlyProvidedBy(request))
    
    # Update the path and query string to reflect the new value
    request_clone.environ['PATH_INFO'] = url_parts.path
    request_clone.environ['QUERY_STRING'] = url_parts.query
    
    request_clone.processInputs()
    
    return request_clone
    

def traverse(request, path):
    """Traverse to the given URL, simulating URL traversal.
    
    Returns the traversed-to object. May raise Unauthorized or NotFound.
    
    If invoke is true, the object will be called
    """
    
    return request.traverse(path)
    
def invoke(request, traversed):
    """Invoke a traversed-to object in the same manner that the publisher
    would.
    """
    
    return mapply(traversed, positional=request.args,
                  keyword=request,
                  debug=None,
                  maybe=1,
                  missing_name=missing_name,
                  handle_class=dont_publish_class,
                  context=request,
                  bind=1)

def resolve(request, url):
    """Resolve the given URL to an lxml tree.
    """
    
    request_clone = clone_request(request, url)
    path = '/'.join(request_clone.physicalPathFromURL(url.split('?')[0]))
    
    try:
        traversed = traverse(request_clone, path)
        resolved = invoke(request_clone, traversed)
    except (NotFound, Unauthorized,), e:
        logger.exception("Could not resolve tile with URL %s" % url)
        request_clone.close()
        return None
    
    request_clone.close()
    
    charset = 'utf-8'
    if 'content-type' in request.response.headers:
        for item in request.response.headers['content-type'].split(';'):
            if item.strip().startswith('charset'):
                charset = item.split('=')[1].strip()
                break
    
    parser = html.HTMLParser()
    if isinstance(resolved, unicode):
        parser.feed(resolved)
    elif isinstance(resolved, str):
        parser.feed(resolved.decode(charset))
    
    root = parser.close()
    return root.getroottree()

def xpath1(xpath, node, strict=True):
    """Return a single node matched by the given etree.XPath object.
    """
    result = xpath(node)
    if len(result) == 1:
        return result[0]
    else:
        if (len(result) > 1 and strict) or len(result) == 0:
            return None
        else:
            return result

def merge_head(src_tree, dest_tree, header_replace, header_append):
    """Merge the <head /> sections.
    
     - Any node in the source matching an xpath in the list header_replace
        will be appended to dest's head. If there is a corresponding tag
        in the dest already, it will be removed.
        
     - Any node in the source matching an xpath in the list header_append will
        be appended to dest's head regardless of whether a corresponding
        tag exists there already.
    """
    
    src_head = xpath1(head_xpath, src_tree)
    dest_head = xpath1(head_xpath, dest_tree)
    
    if src_head is None or dest_head is None:
        return
    
    for replace_xpath in header_replace:
        dest_tags = replace_xpath(dest_tree)
        src_tags = replace_xpath(src_tree)
        if len(src_tags) > 0:
            for dest_tag in dest_tags:
                dest_tag.getparent().remove(dest_tag)
            for src_tag in src_tags:
                dest_head.append(src_tag)

    for append_xpath in header_append:
        for src_tag in append_xpath(src_tree):
            dest_head.append(src_tag)