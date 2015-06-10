# -*- coding: utf-8 -*-
from Acquisition import aq_parent
from OFS.interfaces import ITraversable
from Products.CMFCore.utils import getToolByName
from plone.app.blocks.interfaces import DEFAULT_AJAX_LAYOUT_REGISTRY_KEY
from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
from plone.app.blocks.interfaces import SITE_LAYOUT_FILE_NAME
from plone.app.blocks.interfaces import SITE_LAYOUT_MANIFEST_FORMAT
from plone.app.blocks.interfaces import SITE_LAYOUT_RESOURCE_NAME
from plone.app.blocks.layoutbehavior import SiteLayoutView
from plone.app.blocks.utils import getDefaultAjaxLayout
from plone.app.blocks.utils import getDefaultSiteLayout
from plone.app.blocks.utils import getLayoutAwareSiteLayout
from plone.app.blocks.utils import resolveResource
from plone.memoize import view
from plone.memoize import volatile
from plone.registry.interfaces import IRecordModifiedEvent
from plone.resource.manifest import getAllResources
from plone.resource.traversal import ResourceTraverser
from plone.subrequest import ISubRequest
from zExceptions import NotFound
from zope.annotation import IAnnotations
from zope.component import adapter
from zope.globalrequest import getRequest
from zope.interface import implements
from zope.publisher.browser import BrowserView
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary
from zope.site.hooks import getSite
import Globals
import urlparse


class SiteLayoutTraverser(ResourceTraverser):
    """The site layout traverser.

    Allows traveral to /++sitelayout++<name> using ``plone.resource`` to fetch
    things stored either on the filesystem or in the ZODB.
    """

    name = SITE_LAYOUT_RESOURCE_NAME


class AnnotationsDict(dict):
    """Volatile annotations dictionary to pass to view.memoize_contextless when
    request thread local is not set"""
    implements(IAnnotations)


class _AvailableLayoutsVocabulary(object):
    """Vocabulary to return request cached available layouts of a given type
    """

    implements(IVocabularyFactory)

    def __init__(self, format, defaultFilename):
        self.format = format
        self.defaultFilename = defaultFilename
        self.request = getRequest() or AnnotationsDict()

    @view.memoize_contextless
    def __call__(self, context):
        items = {}  # dictionary is used here to avoid duplicate tokens

        resources = getAllResources(self.format)
        for name, manifest in resources.items():
            title = name.capitalize().replace('-', ' ').replace('.', ' ')
            filename = self.defaultFilename

            if manifest is not None:
                title = manifest['title'] or title
                filename = manifest['file'] or filename
                variants = manifest.get('variants') or []
            else:
                variants = []

            path = "/++%s++%s/%s" % (self.format.resourceType, name, filename)
            items[name] = SimpleTerm(path, name, title)

            for key, value in dict(variants).items():
                key_ = title_ = key.capitalize().replace('_', ' ')
                name_ = '{0:s}-{1:s}'.format(name, key)
                if manifest is not None and manifest['title']:
                    title_ = u'{0:s} ({1:s})'.format(title, key_)
                path = "/++%s++%s/%s" % (self.format.resourceType, name, value)
                items[name_] = SimpleTerm(path, name_, title_)

        items = sorted(items.values(), key=lambda term: term.title)
        return SimpleVocabulary(items)


class AvailableLayoutsVocabulary(object):
    """Vocabulary to return available layouts of a given type
    """

    implements(IVocabularyFactory)

    def __init__(self, format, defaultFilename):
        self.format = format
        self.defaultFilename = defaultFilename

    def __call__(self, context):
        # Instantiate the factory impl per call to support caching by request
        fab = _AvailableLayoutsVocabulary(self.format, self.defaultFilename)
        return fab(context)


AvailableSiteLayoutsVocabularyFactory = AvailableLayoutsVocabulary(
    SITE_LAYOUT_MANIFEST_FORMAT,
    SITE_LAYOUT_FILE_NAME,
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
            if ISubRequest.providedBy(self.request):
                return SiteLayoutView(
                    self.context, self.request.PARENT_REQUEST)()
            else:
                return SiteLayoutView(self.context, self.request)()

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
        if self.request.form.get('ajax_load'):
            return getDefaultAjaxLayout(self.context)
        else:
            return getDefaultSiteLayout(self.context)


class PageSiteLayout(DefaultSiteLayout):
    """Look up and render the site layout to use for the context.

    Use this for a page that does have the ILayout behavior. It will take the
    ``pageSiteLayout`` property into account.

    The idea is that you can do:

        <html data-layout="./@@page-site-layout">

    and always get the correct site layout for the page, taking section-
    and page-specific settings into account.
    """

    def _getLayout(self):
        if self.request.form.get('ajax_load'):
            return getDefaultAjaxLayout(self.context)
        else:
            return getLayoutAwareSiteLayout(self.context)
