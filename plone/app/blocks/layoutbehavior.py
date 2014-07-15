# -*- coding: utf-8 -*-
import os
import logging

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.globals.interfaces import IViewView
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from zope.interface import implements
from zope.interface import alsoProvides
from zope import schema

from plone.app.blocks.interfaces import ILayoutField
from plone.app.blocks.interfaces import IBlocksTransformEnabled
from plone.app.blocks.interfaces import IOmittedField
from plone.app.blocks.interfaces import _


logger = logging.getLogger('plone.app.blocks')


class LayoutField(schema.Text):
    """A field used to store layout information
    """

    implements(ILayoutField)


class ILayoutAware(model.Schema):
    """Behavior interface to make a type support layout.
    """
    content = LayoutField(
        title=_(u"Custom layout"),
        description=_(u"Custom content and content layout of this page"),
        required=False,
    )

    pageSiteLayout = schema.Choice(
        title=_(u"Site layout"),
        description=_(u"Site layout to apply to this page "
                      u"instead of the default site layout"),
        vocabulary="plone.availableSiteLayouts",
        required=False,
    )

    sectionSiteLayout = schema.Choice(
        title=_(u"Section site layout"),
        description=_(u"Site layout to apply to sub-pages of this page "
                      u"instead of the default site layout"),
        vocabulary="plone.availableSiteLayouts",
        required=False,
    )

    fieldset('layout', label=_('Layout'),
             fields=('content', 'pageSiteLayout', 'sectionSiteLayout'))

alsoProvides(ILayoutAware, IFormFieldProvider)

alsoProvides(ILayoutAware['content'], IOmittedField)
alsoProvides(ILayoutAware['pageSiteLayout'], IOmittedField)
alsoProvides(ILayoutAware['sectionSiteLayout'], IOmittedField)


class SiteLayoutView(BrowserView):
    """Default site layout view called from the site layout resolving view"""

    implements(IViewView)

    index = ViewPageTemplateFile(os.path.join('templates', 'main_template.pt'))

    def __call__(self):
        self.__name__ = 'main_template'
        return self.index()


class ContentLayoutView(BrowserView):
    """Default view for a layout aware page
    """

    implements(IBlocksTransformEnabled)

    def __init__(self, context, request):
        super(ContentLayoutView, self).__init__(context, request)

    def __call__(self):
        """Render the contents of the "content" field coming from
        the ILayoutAware behavior.

        This result is supposed to be transformed by plone.app.blocks.
        """
        return ILayoutAware(self.context).content
