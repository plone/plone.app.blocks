# -*- coding: utf-8 -*-
import os
import logging

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.globals.interfaces import IViewView
from plone.autoform.interfaces import IFormFieldProvider
from plone.dexterity.browser.view import DefaultView
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from zope.component import adapter, getMultiAdapter
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
from zope.interface import implements, provider
from zope.interface import implementer
from zope.interface import Interface
from zope.interface import alsoProvides
from zope import schema
from zope.schema._bootstrapinterfaces import IContextAwareDefaultFactory

from plone.app.blocks.interfaces import IBlocksTransformEnabled
from plone.app.blocks.interfaces import ILayoutField
from plone.app.blocks.interfaces import ILayoutFieldDefaultValue
from plone.app.blocks.interfaces import IOmittedField
from plone.app.blocks.interfaces import _


logger = logging.getLogger('plone.app.blocks')


class LayoutField(schema.Text):
    """A field used to store layout information
    """

    implements(ILayoutField)


@implementer(ILayoutFieldDefaultValue)
@adapter(Interface, Interface)
def layoutFieldDefaultValue(context, request):
    import pdb; pdb.set_trace()
    return u"""\
<!DOCTYPE html>
<html lang="en" data-layout="./@@page-site-layout">
<body>
<div data-panel="content">
</div>
</body>
</html>"""


@provider(IContextAwareDefaultFactory)
def layoutFieldDefaultValueFactory(context):
    if context is None:
        context = getSite()
    request = getRequest()
    return getMultiAdapter((context, request), ILayoutFieldDefaultValue)


class ILayoutAware(model.Schema):
    """Behavior interface to make a type support layout.
    """
    content = LayoutField(
        title=_(u"Custom layout"),
        description=_(u"Custom content and content layout of this page"),
        defaultFactory=layoutFieldDefaultValueFactory,
        required=False
    )

    pageSiteLayout = schema.Choice(
        title=_(u"Site layout"),
        description=_(u"Site layout to apply to this page "
                      u"instead of the default site layout"),
        vocabulary="plone.availableSiteLayouts",
        required=False
    )

    sectionSiteLayout = schema.Choice(
        title=_(u"Section site layout"),
        description=_(u"Site layout to apply to sub-pages of this page "
                      u"instead of the default site layout"),
        vocabulary="plone.availableSiteLayouts",
        required=False
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

    index = ViewPageTemplateFile(os.path.join('templates',
                                              'main_template.pt'))

    def __call__(self):
        self.__name__ = 'main_template'
        return self.index()


class ContentLayoutView(DefaultView):
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
