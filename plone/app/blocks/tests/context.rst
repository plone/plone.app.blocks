If a relative URL for the layout is specified, the context the site layout
browser view will use to be rendered (e.g. to resolve TAL expressions) will be
determined in relation to the object where the page layout view is called.

To illustrate this, we create two browser views with the context title (which
will be the Plone site itself) as part of the title and contents of the site
and page layouts, respectively::

    >>> from zope.publisher.browser import BrowserView

    >>> class SiteLayout(BrowserView):
    ...     __name__ = 'site-layout'
    ...	    def __call__(self):
    ...         return u"""
    ... <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    ... <html>
    ...   <head>
    ...     <title>%s</title>
    ...   </head>
    ...   <body>
    ...     <div data-panel="content">Site layout content</div>
    ...   </body>
    ... </html>
    ... """ % self.context.Title()

    >>> from zope.interface import implements
    >>> from plone.app.blocks.interfaces import IBlocksTransformEnabled
    >>> class PageLayout(BrowserView):
    ...     implements(IBlocksTransformEnabled)
    ...     __name__ = 'page-layout'
    ...	    def __call__(self):
    ...         return u"""
    ... <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    ... <html data-layout="./@@site-layout">
    ...   <head></head>
    ...   <body>
    ...     <div data-panel="content">%s</div>
    ...   </body>
    ... </html>
    ... """ % self.context.Title()

Observe that the ``<html data-layout="./@@site-layout">`` tag references a
relative URL.

Next, we initialize and register the browser views as ZCML handlers would::

    >>> from zope.interface import Interface
    >>> from Products.Five.security import protectClass
    >>> protectClass(SiteLayout, 'zope2.View')
    >>> protectClass(PageLayout, 'zope2.View')

    >>> from App.class_init import InitializeClass
    >>> InitializeClass(SiteLayout)
    >>> InitializeClass(PageLayout)

    >>> from zope.component import provideAdapter
    >>> provideAdapter(SiteLayout, (Interface, Interface,), Interface, u'site-layout')
    >>> provideAdapter(PageLayout, (Interface, Interface,), Interface, u'page-layout')

If we now render the page calling it with the portal object itself as context,
the default title of the portal object, ``Plone site`` will be used::

    >>> from plone.testing.z2 import Browser
    >>> app = layer['app']
    >>> browser = Browser(app)
    >>> browser.handleErrors = False

    >>> portal = layer['portal']
    >>> browser.open(portal.absolute_url() + '/@@page-layout')
    >>> print browser.contents
    <!DOCTYPE html...
        <title>Plone site</title>...
        <div data-panel="content">Plone site</div>...
