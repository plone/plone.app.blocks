# -*- coding: utf-8 -*-
from plone.app.blocks.interfaces import IBlocksTransformEnabled
from plone.app.blocks.utils import getLayout
from plone.app.layout.globals.interfaces import IViewView
from plone.dexterity.browser.view import DefaultView
from plone.outputfilters import apply_filters
from plone.outputfilters.interfaces import IFilter
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getAdapters
from zope.interface import implementer

import os


ERROR_LAYOUT = u"""
<!DOCTYPE html>
<html lang="en" data-layout="./@@page-site-layout">
<body>
    <div data-panel="content">
        Could not find layout for content
    </div>
</body>
</html>"""


@implementer(IViewView)
class SiteLayoutView(BrowserView):
    """Default site layout view called from the site layout resolving view"""

    index = ViewPageTemplateFile(
        os.path.join('templates', 'main_template.pt')
    )

    def __init__(self, context, request, name='layout'):
        super(SiteLayoutView, self).__init__(context, request)
        self.__name__ = name

    def __call__(self):
        return self.index()


@implementer(IBlocksTransformEnabled)
class ContentLayoutView(DefaultView):
    """Default view for a layout aware page
    """

    def __call__(self):
        """Render the contents of the "content" field coming from
        the ILayoutAware behavior.

        This result is supposed to be transformed by plone.app.blocks.
        """
        layout = getLayout(self.context)

        if not layout:
            layout = ERROR_LAYOUT

        # Here we skip legacy portal_transforms and call plone.outputfilters
        # directly by purpose
        filters = [
            f for _, f in getAdapters((self.context, self.request), IFilter)
        ]
        return apply_filters(filters, layout)
