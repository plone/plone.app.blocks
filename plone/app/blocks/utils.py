import logging
from urlparse import urlsplit, urljoin
import uuid

from zope.interface import directlyProvidedBy, directlyProvides
from zope.component import queryMultiAdapter

from AccessControl import Unauthorized
from zExceptions import NotFound

try:
    from repoze.zope2.mapply import mapply, missing_name, dont_publish_class
except ImportError:
    from ZPublisher.mapply import mapply
    from ZPublisher.Publish import missing_name, dont_publish_class

from lxml import etree
from lxml import html

headXPath = etree.XPath("/html/head")
layoutXPath = etree.XPath("/html/head/link[@rel='layout']")
tileXPath = etree.XPath("/html/head/link[@rel='tile']")
panelXPath = etree.XPath("/html/head/link[@rel='panel']")

logger = logging.getLogger('plone.app.blocks')


def cloneRequest(request, url):
    """Clone the given request for use in traversal to the given URL.

    This will set up request.form as well.

    The returned request should be cleard with request.clear(). It should
    *not* be closed with request.close(), since this fires EndRequestEvent,
    which in turn disables the site-local component registry.
    """
    #  normalise url and split query string
    urlParts = urlsplit(url)

    # Clone the request so that we can traverse from it.

    requestClone = request.clone()

    # Make sure the new request provides the same markers as our old one
    directlyProvides(requestClone, *directlyProvidedBy(request))

    # Update the path and query string to reflect the new value
    requestClone.environ['PATH_INFO'] = urlParts.path
    requestClone.environ['QUERY_STRING'] = urlParts.query

    requestClone.processInputs()

    return requestClone


def traverse(request, path):
    """Traverse to the given URL, simulating URL traversal.

    Returns the traversed-to object. May raise Unauthorized or NotFound.
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


def resolve(request, url, renderView=None, renderedRequestKey=None):
    """Resolve the given URL to an lxml tree.

    If ``renderView`` is given, it should be the name of a view that will be
    looked up for the item being traversed to (e.g.a  tile). If the lookup
    succeeds, this view will be used for the returned body instead of calling
    the traversed object as normal.

    If ``renderView`` is used, a key with the name given by
    ``renderedRequestKey`` will be set to True in the request.
    """

    requestClone = cloneRequest(request, url)
    path = '/'.join(requestClone.physicalPathFromURL(url.split('?')[0]))

    try:
        traversed = traverse(requestClone, path)
        renderer = queryMultiAdapter((traversed, requestClone,),
                                     name=renderView)
        if renderer is not None:
            if renderedRequestKey is not None:
                request.set(renderedRequestKey, True)
            traversed = renderer

        resolved = invoke(requestClone, traversed)
    except (NotFound, Unauthorized,):
        logger.exception("Could not resolve tile with URL %s" % url)
        requestClone.clear()
        return None

    charset = extractCharset(requestClone.response)
    requestClone.clear()

    if isinstance(resolved, str):
        resolved = resolved.decode(charset)

    return html.fromstring(resolved).getroottree()


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
    """ Sort entries from findTiles on ID """

    return cmp(tile0[0], tile1[0])
