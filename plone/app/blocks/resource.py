# -*- coding: utf-8 -*-
from Acquisition import aq_parent
from ConfigParser import SafeConfigParser
from OFS.interfaces import ITraversable
from plone.app.blocks.interfaces import CONTENT_LAYOUT_FILE_NAME
from plone.app.blocks.interfaces import CONTENT_LAYOUT_MANIFEST_FORMAT
from plone.app.blocks.interfaces import CONTENT_LAYOUT_RESOURCE_NAME
from plone.app.blocks.interfaces import DEFAULT_AJAX_LAYOUT_REGISTRY_KEY
from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
from plone.app.blocks.interfaces import SITE_LAYOUT_FILE_NAME
from plone.app.blocks.interfaces import SITE_LAYOUT_MANIFEST_FORMAT
from plone.app.blocks.interfaces import SITE_LAYOUT_RESOURCE_NAME
from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.layoutviews import SiteLayoutView
from plone.app.blocks.utils import resolveResource
from plone.memoize import view
from plone.memoize import volatile
from plone.registry.interfaces import IRecordModifiedEvent
from plone.resource.manifest import MANIFEST_FILENAME
from plone.resource.traversal import ResourceTraverser
from plone.resource.utils import iterDirectoriesOfType
from plone.subrequest import ISubRequest
from Products.CMFCore.utils import getToolByName
from zExceptions import NotFound
from zope.annotation import IAnnotations
from zope.component import adapter
from zope.globalrequest import getRequest
from zope.interface import implementer
from zope.publisher.browser import BrowserView
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.site.hooks import getSite

import Globals
import logging
import urlparse


logger = logging.getLogger('plone.app.blocks')


class SiteLayoutTraverser(ResourceTraverser):
    """The site layout traverser.

    Allows traveral to /++sitelayout++<name> using ``plone.resource`` to fetch
    things stored either on the filesystem or in the ZODB.
    """

    name = SITE_LAYOUT_RESOURCE_NAME


class ContentLayoutTraverser(ResourceTraverser):
    """The content layout traverser.

    Allows traversal to /++contentlayout++<name> using ``plone.resource`` to
    fetch things stored either on the filesystem or in the ZODB.
    """

    name = CONTENT_LAYOUT_RESOURCE_NAME


@implementer(IAnnotations)
class AnnotationsDict(dict):
    """Volatile annotations dictionary to pass to view.memoize_contextless when
    request thread local is not set"""


class multidict(dict):
    """
    Taken from: http://stackoverflow.com/questions/9876059/parsing-configure-file-with-same-section-name-in-python  # noqa
    """
    _unique = 0

    def __setitem__(self, key, val):
        if isinstance(val, dict):
            self._unique += 1
            key += str(self._unique)
        dict.__setitem__(self, key, val)


def getLayoutsFromManifest(fp, _format, directory_name):
    parser = SafeConfigParser(None, multidict)
    parser.readfp(fp)

    layouts = {}
    for section in parser.sections():
        if not section.startswith(_format.resourceType) or \
           ':variants' in section:
            continue
        # id is a combination of directory name + filename
        if parser.has_option(section, 'file'):
            filename = parser.get(section, 'file')
        else:
            filename = ''  # this should not happen...
        _id = directory_name + '/' + filename
        if _id in layouts:
            # because TTW resources are created first, we consider layouts
            # with same id in a TTW to be taken before other resources
            continue
        data = {
            'directory': directory_name
        }
        for key in _format.keys:
            if parser.has_option(section, key):
                data[key] = parser.get(section, key)
            else:
                data[key] = _format.defaults.get(key, None)
        layouts[_id] = data

    return layouts


def getLayoutsFromDirectory(directory, _format):
    layouts = {}
    name = directory.__name__
    if directory.isFile(MANIFEST_FILENAME):
        manifest = directory.openFile(MANIFEST_FILENAME)
        try:
            layouts.update(getLayoutsFromManifest(manifest, _format, name))
        except:
            logger.exception(
                "Unable to read manifest for theme directory %s", name)
        finally:
            manifest.close()
    else:
        # can provide default file for it with no manifest
        filename = _format.defaults.get('file', '')
        if filename and directory.isFile(filename):
            _id = name + '/' + filename
            if _id not in layouts:
                # not overridden
                title = name.capitalize().replace('-', ' ').replace('.', ' ')
                layouts[_id] = {
                    'title': title,
                    'description': '',
                    'directory': name,
                    'file': _format.defaults.get('file', '')
                }
    return layouts


def getLayoutsFromResources(_format):
    layouts = {}

    for directory in iterDirectoriesOfType(_format.resourceType):
        layouts.update(getLayoutsFromDirectory(directory, _format))

    return layouts


@implementer(IVocabularyFactory)
class _AvailableLayoutsVocabulary(object):
    """Vocabulary to return request cached available layouts of a given type
    """

    def __init__(self):
        self.request = getRequest() or AnnotationsDict()

    @view.memoize_contextless
    def __call__(self, context, format, defaultFilename):
        items = {}  # dictionary is used here to avoid duplicate tokens

        resources = getLayoutsFromResources(format)
        used = []
        for _id, config in resources.items():
            title = config.get('title', _id)
            filename = config.get('file', defaultFilename)

            path = "/++%s++%s/%s" % (format.resourceType,
                                     config['directory'], filename)
            if path in used:
                # term values also need to be unique
                # this should not happen but it's possible for users to screw
                # up their layout definitions and it's better to not error here
                continue
            used.append(path)
            items[_id] = SimpleTerm(path, _id, title)

        items = sorted(items.values(), key=lambda term: term.title)
        return SimpleVocabulary(items)


@implementer(IVocabularyFactory)
class AvailableLayoutsVocabulary(object):
    """Vocabulary to return available layouts of a given type
    """

    def __init__(self, format, defaultFilename):
        self.format = format
        self.defaultFilename = defaultFilename

    def __call__(self, context):
        # Instantiate the factory impl per call to support caching by request
        fab = _AvailableLayoutsVocabulary()
        return fab(context, self.format, self.defaultFilename)


AvailableSiteLayoutsVocabularyFactory = AvailableLayoutsVocabulary(
    SITE_LAYOUT_MANIFEST_FORMAT,
    SITE_LAYOUT_FILE_NAME,
)

AvailableContentLayoutsVocabularyFactory = AvailableLayoutsVocabulary(
    CONTENT_LAYOUT_MANIFEST_FORMAT,
    CONTENT_LAYOUT_FILE_NAME,
)


def cacheKey(method, self):
    """Invalidate if the fti is modified, the global registry is modified,
    or the content is modified
    """

    if Globals.DevelopmentMode:
        raise volatile.DontCache()

    catalog = getToolByName(self.context, 'portal_catalog')

    return (
        getattr(self.context, '_p_mtime', None),
        self.request.form.get('ajax_load'),
        catalog.getCounter(),
    )


@adapter(IRecordModifiedEvent)
def globalSiteLayoutModified(event):
    """Invalidate caches if the global site layout is changed. This will
    likely also affect things cached using plone.app.caching, which is what
    we want - the page has probably changed
    """
    if event.record.__name__ in (DEFAULT_SITE_LAYOUT_REGISTRY_KEY,
                                 DEFAULT_AJAX_LAYOUT_REGISTRY_KEY):
        if event.oldValue != event.newValue:
            catalog = getToolByName(getSite(), 'portal_catalog', None)
            if catalog is not None and hasattr(catalog, '_increment_counter'):
                catalog._increment_counter()


class DefaultSiteLayout(BrowserView):
    """Look up and render the site layout to use for the context.

    Use this for a page that does not have the ILayout behavior, or a
    standalone page template.

    The idea is that you can do:

        <html data-layout="./@@default-site-layout">

    and always get the correct site layout for the page, taking section-
    specific settings into account.
    """

    def __call__(self):
        try:
            return self.index()
        except NotFound:
            pass
        request = self.request
        if ISubRequest.providedBy(request):
            request = request.PARENT_REQUEST
        return SiteLayoutView(self.context, request)()

    @property
    @volatile.cache(cacheKey, volatile.store_on_context)
    def layout(self):
        layout = self._getLayout()
        if layout is None:
            raise NotFound("No default site layout set")

        pathContext = self.context
        while not ITraversable.providedBy(pathContext):
            pathContext = aq_parent(pathContext)
            if pathContext is None:
                break

        path = layout
        if pathContext is not None:
            path = urlparse.urljoin(pathContext.absolute_url_path(), layout)

        return path

    @volatile.cache(cacheKey, volatile.store_on_context)
    def index(self):
        return resolveResource(self.layout)

    def _getLayout(self):
        layout_adapter = ILayoutAware(self.context)
        if self.request.form.get('ajax_load'):
            return layout_adapter.ajax_site_layout()
        return layout_adapter.site_layout()


class PageSiteLayout(DefaultSiteLayout):
    """Look up and render the site layout to use for the context.

    Use this for a page that does have the ILayout behavior. It will take the
    ``pageSiteLayout`` property into account.

    The idea is that you can do:

        <html data-layout="./@@page-site-layout">

    and always get the correct site layout for the page, taking section-
    and page-specific settings into account.
    """
