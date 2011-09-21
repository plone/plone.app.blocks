import logging
import uuid

from urlparse import urljoin

from lxml import etree
from lxml import html

from zope.component import queryUtility
from zope.site.hooks import getSite

from plone.subrequest import subrequest

from plone.registry.interfaces import IRegistry

from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
from plone.app.blocks.layoutbehavior import ILayoutAware

from Acquisition import aq_inner
from Acquisition import aq_parent

from zExceptions import NotFound

from Products.CMFCore.utils import getToolByName

headXPath = etree.XPath("/html/head")
layoutXPath = etree.XPath("/html/head/link[@rel='layout']")
headTileXPath = etree.XPath("/html/head/link[@rel='tile']")
panelXPath = etree.XPath("/html/head/link[@rel='panel']")

logger = logging.getLogger('plone.app.blocks')

def extractCharset(response, default='utf-8'):
    """Get the charset of the given response
    """

    charset = default
    if 'content-type' in response.headers:
        for item in response.headers['content-type'].split(';'):
            if item.strip().startswith('charset'):
                charset = item.split('=')[1].strip()
                break
    return charset


def resolve(url):
    """Resolve the given URL to an lxml tree.
    """
    
    resolved = resolveResource(url)
    return html.fromstring(resolved).getroottree()

def resolveResource(url):
    """Resolve the given URL to a unicode string. If the URL is an absolute
    path, it will be made relative to the Plone site root.
    """
    if url.startswith('/'):
        site = getSite()
        portal_url = getToolByName(site, 'portal_url')
	url = '/'.join(site.getPhysicalPath()) + url

    response = subrequest(url)
    if response.status == 404:
        raise NotFound(url)
    
    resolved = response.getBody()
    
    if isinstance(resolved, str):
        charset = extractCharset(response)
        resolved = resolved.decode(charset)
    
    if response.status != 200:
        raise RuntimeError(resolved)
    
    return resolved


def xpath1(xpath, node, strict=True):
    """Return a single node matched by the given etree.XPath object.
    """

    if isinstance(xpath, basestring):
        xpath = etree.XPath(xpath)

    result = xpath(node)
    if len(result) == 1:
        return result[0]
    else:
        if (len(result) > 1 and strict) or len(result) == 0:
            return None
        else:
            return result


def mergeHead(srcTree, destTree, headerReplace, headerAppend):
    """Merge the <head /> sections.

     - Any node in the source matching an xpath in the list headerReplace
        will be appended to dest's head. If there is a corresponding tag
        in the dest already, it will be removed.

     - Any node in the source matching an xpath in the list headerAppend will
        be appended to dest's head regardless of whether a corresponding
        tag exists there already.
    """

    srcHead = xpath1(headXPath, srcTree)
    destHead = xpath1(headXPath, destTree)

    if srcHead is None or destHead is None:
        return

    for replaceXPath in headerReplace:
        destTags = replaceXPath(destTree)
        srcTags = replaceXPath(srcTree)
        if len(srcTags) > 0:
            for destTag in destTags:
                destTag.getparent().remove(destTag)
            for srcTag in srcTags:
                destHead.append(srcTag)

    for appendXPath in headerAppend:
        for srcTag in appendXPath(srcTree):
            destHead.append(srcTag)


def findTiles(request, tree, removeHeadLinks=False, ignoreHeadTiles=False):
    """Given a request and an lxml tree with the body, return a list of
    tuples of tile id, absolute tile href (including query string) and the
    tile placeholder node.

    If removeHeadLinks is true, tile links in the head are removed once
    complete. This is useful if we know that the tile's head will be merged
    into the rendered head anyway. In this case, the tile placeholder node 
    will be None.
    
    If ignoreHeadTiles is true, tile links in the head are ignored entirely.
    """
    
    tiles = []
    baseURL = request.getURL()

    # Find tiles in the head of the page
    if not ignoreHeadTiles or removeHeadLinks:
        for tileNode in headTileXPath(tree):
            tileHref = tileNode.get('href', None)

            if tileHref is not None:
                tileId = "__tile_%s" % uuid.uuid4()
                tileHref = urljoin(baseURL, tileHref)
            
                if removeHeadLinks:
                    tileNode.getparent().remove(tileNode)
                    tileNode = None
                
                if not ignoreHeadTiles:
                    tiles.append((tileId, tileHref, tileNode,))

    # Find tiles in the body
    for tileNode in tree.getroot().cssselect(".tile-placeholder"):
        tileId = tileNode.get('id', None)
        tileHref = tileNode.get('data-tile-href', None)

        if tileHref is not None:
            
            # If we do not have an id, generate one
            if tileId is None:
                tileId = "__tile_%s" % uuid.uuid4()
                tileNode.attrib['id'] = tileId
            
            tileHref = urljoin(baseURL, tileHref)
            tiles.append((tileId, tileHref, tileNode,))

    return tiles

def getDefaultSiteLayout(context):
    """Get the path to the site layout to use by default for the given content
    object
    """
    
    # Note: the sectionSiteLayout on context is for pages *under* context, not
    # necessarily context itself

    parent = aq_parent(aq_inner(context))
    while parent is not None:
        layoutAware = ILayoutAware(parent, None)
        if layoutAware is not None:
            if getattr(layoutAware, 'sectionSiteLayout', None):
                return layoutAware.sectionSiteLayout
        parent = aq_parent(aq_inner(parent))
    
    registry = queryUtility(IRegistry)
    if registry is None:
        return None
    
    return registry.get(DEFAULT_SITE_LAYOUT_REGISTRY_KEY)

def getLayoutAwareSiteLayout(context):
    """Get the path to the site layout for a page. This is generally only
    appropriate for the view of this page. For a generic template or view, use
    getDefaultSiteLayout(context) instead.
    """
    
    layoutAware = ILayoutAware(context, None)
    if layoutAware is not None:
        if getattr(layoutAware, 'pageSiteLayout', None):
            return layoutAware.pageSiteLayout
    
    return getDefaultSiteLayout(context)
