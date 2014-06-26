# -*- coding: utf-8 -*-
import logging

from Products.Five import BrowserView
from plone.autoform.directives import mode
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from plone.supermodel.directives import fieldset
from z3c.form.interfaces import HIDDEN_MODE
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
        description=_(u"Site layout to apply to this page"),
        vocabulary="plone.availableSiteLayouts",
        required=False,
    )

    sectionSiteLayout = schema.Choice(
        title=_(u"Section site layout"),
        description=_(u"Site layout to apply to sub-pages of this page"),
        vocabulary="plone.availableSiteLayouts",
        required=False,
    )

    fieldset('layout', label=_('Layout'),
             fields=('content', 'pageSiteLayout', 'sectionSiteLayout'))

alsoProvides(ILayoutAware, IFormFieldProvider)

alsoProvides(ILayoutAware['content'], IOmittedField)
alsoProvides(ILayoutAware['pageSiteLayout'], IOmittedField)
alsoProvides(ILayoutAware['sectionSiteLayout'], IOmittedField)


class LayoutView(BrowserView):
    """Default view for a layout aware page
    """

    implements(IBlocksTransformEnabled)

    def __init__(self, context, request):
        super(LayoutView, self).__init__(context, request)

    def __call__(self):
        """Render the contents of the "content" field coming from
        the ILayoutAware behavior.

        This result is supposed to be transformed by plone.app.blocks.
        """
        return ILayoutAware(self.context).content
