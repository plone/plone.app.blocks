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
tileXPath = etree.XPath("/html/head/link[@rel='tile']")
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
        url = portal_url.getPortalObject().absolute_url_path() + url
    
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


def findTiles(request, tree, remove=False):

    """Given a request and an lxml tree with the body, return a dict
    of tile id to a tuple of absolute tile href (including query
    string) and a marker specifying whether this is a tile with an
    actual target or not. The latter is needed for tiles that need to
    only merge into the head.

    If remove is true, tile links are removed once complete.
    """

    tiles = {}
    baseURL = request.getURL()

    # Find all tiles that exist in the page
    for tileNode in tileXPath(tree):

        # If we do not have an id, generate one
        tileId = tileNode.get('target', None)
        tileHref = tileNode.get('href', None)
        hasTarget = True

        if tileId is None:
            tileId = "__tile_%s" % uuid.uuid1()
            hasTarget = False

        if tileHref is not None:
            tileHref = urljoin(baseURL, tileHref)
            tileTargetXPath = etree.XPath("//*[@id='%s']" % tileId)
            tileTargetNode = xpath1(tileTargetXPath, tree)
            if (not hasTarget) or (tileTargetNode is not None):
                tiles[tileId] = (tileHref, hasTarget)

        if remove:
            tileNode.getparent().remove(tileNode)

    return tiles


def tileSort(tile0, tile1):
    """Sort entries from findTiles on ID
    """

    return cmp(tile0[0], tile1[0])

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
