# -*- coding: utf-8 -*-
from Acquisition import aq_inner
from Acquisition import aq_parent
from plone.app.blocks.interfaces import _
from plone.app.blocks.interfaces import DEFAULT_AJAX_LAYOUT_REGISTRY_KEY
from plone.app.blocks.interfaces import DEFAULT_CONTENT_LAYOUT_REGISTRY_KEY
from plone.app.blocks.interfaces import DEFAULT_SITE_LAYOUT_REGISTRY_KEY
from plone.app.blocks.interfaces import ILayoutField
from plone.app.blocks.utils import applyTilePersistent
from plone.app.blocks.utils import resolveResource
from plone.autoform.directives import write_permission
from plone.autoform.interfaces import IFormFieldProvider
from plone.registry.interfaces import IRegistry
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from zExceptions import NotFound
from zope import schema
from zope.component import adapter
from zope.component import getUtility
from zope.component import queryUtility
from zope.deprecation import deprecate
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import provider

import logging
import zope.deferredimport

logger = logging.getLogger('plone.app.blocks')

zope.deferredimport.deprecated(
    'Moved in own module due to avoid circular imports. '
    'Import from plone.app.blocks.layoutviews instead',
    SiteLayoutView='plone.app.blocks.layoutviews:SiteLayoutView',
    ContentLayoutView='plone.app.blocks.layoutviews:ContentLayoutView',
)


@implementer(ILayoutField)
class LayoutField(schema.Text):
    """A field used to store layout information
    """


@provider(IFormFieldProvider)
class ILayoutAware(model.Schema):
    """Behavior interface to make a type support layout.
    """
    content = LayoutField(
        title=_(u"Custom layout"),
        description=_(u"Custom content and content layout of this page"),
        default=None,
        required=False
    )

    contentLayout = schema.ASCIILine(
        title=_(u'Content Layout'),
        description=_(
            u'Selected content layout. If selected, custom layout is '
            u'ignored.'),
        required=False)

    pageSiteLayout = schema.Choice(
        title=_(u"Site layout"),
        description=_(u"Site layout to apply to this page "
                      u"instead of the default site layout"),
        vocabulary="plone.availableSiteLayouts",
        required=False
    )
    write_permission(pageSiteLayout="plone.ManageSiteLayouts")

    sectionSiteLayout = schema.Choice(
        title=_(u"Section site layout"),
        description=_(u"Site layout to apply to sub-pages of this page "
                      u"instead of the default site layout"),
        vocabulary="plone.availableSiteLayouts",
        required=False
    )
    write_permission(sectionSiteLayout="plone.ManageSiteLayouts")

    fieldset(
        'layout',
        label=_('Layout'),
        fields=(
            'content',
            'pageSiteLayout',
            'sectionSiteLayout',
            'contentLayout'
        )
    )

    def content_layout():
        """returns HTML layout of content
        """

    def site_layout():
        """returns resource of the site layout
        """

    def ajax_site_layout(self):
        """Get the path to the ajax site layout to use by default for the given
        content object
        """


class ILayoutBehaviorAdaptable(Interface):
    """Marker Interface for ILayoutAware adaptable content
    """


@implementer(ILayoutAware)
@adapter(Interface)
class LayoutAwareDefault(object):
    """Default layout lookup for a context w/o the behavior
    """

    content = None
    contentLayout = None
    pageSiteLayout = None
    sectionSiteLayout = None

    def __init__(self, context):
        self.context = context

    def content_layout(self):
        layout = None
        registry = getUtility(IRegistry)
        try:
            path = registry['%s.%s' % (
                DEFAULT_CONTENT_LAYOUT_REGISTRY_KEY,
                self.context.portal_type.replace(' ', '-'))]
        except (KeyError, AttributeError):
            path = None
        try:
            path = path or registry[DEFAULT_CONTENT_LAYOUT_REGISTRY_KEY]
            resolved = resolveResource(path)
            layout = applyTilePersistent(path, resolved)
        except (KeyError, NotFound, RuntimeError):
            pass
        return layout

    def site_layout(self):
        """Bubble up looking for an sectionSiteLayout, otherwise lookup the
        global sitelayout.

        Note: the sectionSiteLayout on context is for pages *under* context,
        not necessarily context itself
        """
        parent = aq_parent(aq_inner(self.context))
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

    def ajax_site_layout(self):
        registry = queryUtility(IRegistry)
        if registry is not None:
            return registry.get(DEFAULT_AJAX_LAYOUT_REGISTRY_KEY)
        else:
            return self.context.site_layout


@implementer(ILayoutAware)
@adapter(ILayoutBehaviorAdaptable)
class LayoutAwareBehavior(LayoutAwareDefault):

    def __init__(self, context):
        self.context = context

    @property
    def content(self):
        return getattr(self.context, 'content', None)

    @content.setter
    def content(self, value):
        self.context.content = value

    @property
    def contentLayout(self):
        return getattr(self.context, 'contentLayout', None)

    @contentLayout.setter
    def contentLayout(self, value):
        self.context.contentLayout = value

    @property
    def pageSiteLayout(self):
        return getattr(self.context, 'pageSiteLayout', None)

    @pageSiteLayout.setter
    def pageSiteLayout(self, value):
        self.context.pageSiteLayout = value

    @property
    def sectionSiteLayout(self):
        return getattr(self.context, 'sectionSiteLayout', None)

    @sectionSiteLayout.setter
    def sectionSiteLayout(self, value):
        self.context.sectionSiteLayout = value

    def content_layout(self):
        if self.contentLayout:
            try:
                path = self.contentLayout
                resolved = resolveResource(path)
                return applyTilePersistent(path, resolved)
            except (NotFound, RuntimeError):
                pass
        elif self.content:
            return self.content

        return super(LayoutAwareBehavior, self).content_layout()

    def site_layout(self):
        """Get the path to the site layout for a page.

        This is generally only appropriate for the view of this page.
        For a generic template or view getDefaultSiteLayout(context)
        """
        return self.pageSiteLayout or \
            self.sectionSiteLayout or \
            super(LayoutAwareBehavior, self).site_layout()


@deprecate(
    'adapt with ILayoutAware instead, call adapter.site_layout()'
)
def getLayoutAwareSiteLayout(content):
    lookup = ILayoutAware(content)
    return lookup.content_layout()


@deprecate(
    'adapt with ILayoutAware instead, call adapter.content_layout()'
)
def getLayout(content):
    lookup = ILayoutAware(content)
    return lookup.content_layout()


@deprecate(
    'adapt with ILayoutAware instead. Never depend on the default. '
    'In fact this was meant only for internal use.'
)
def getDefaultSiteLayout(context):
    """Get the path to the site layout to use by default for the given content
    object
    """
    lookup = LayoutAwareDefault(context)
    return lookup.site_layout()


@deprecate(
    'adapt with ILayoutAware instead, call adapter.ajax_site_layout()'
)
def getDefaultAjaxLayout(context):
    """Get the path to the ajax site layout to use by default for the given
    content object
    """
    lookup = ILayoutAware(context)
    return lookup.ajax_site_layout()
