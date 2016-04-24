ESI rendering
=============

Blocks supports rendering of tiles for Edge Side Includes (ESI).
A tile will be rendered to ESI provided that:

* The tile itself is marked with the ``IESIRendered`` marker interface.
  See `plone.tiles`_ for more details.
* The ``plone.app.blocks.interfaces.IBlocksSettings.esi`` record in the registry is set to True.
  It is False by default.
  To switch this through-the-web, you can visit the configuration registry control panel in Plone.

Note that if a tile is rendered using ESI, it's <head /> contents are ignored, instead of being merged into the final page.
That is, only the ``@@esi-body`` view form `plone.tiles`_ is used by default.

An ESI link looks like this:

.. code-block:: xml

    <esi:include src="http://example.com/plone/@@some.tile/tile-1/@@esi-body?param1=value1" />

A fronting server such as Varnish will be able to load this on demand and
compose the page from fragments that may be cached individually.

Test setup
----------

Let's first register a two very simple tiles. One uses ESI, one does not.

.. code-block:: python

    >>> from plone.tiles.esi import ESITile
    >>> from plone.tiles import Tile
    >>> from plone.tiles.type import TileType

    >>> class NonESITile(Tile):
    ...     __name__ = 'test.tile2' # normally set by ZCML handler
    ...
    ...     def __call__(self):
    ...         return """\
    ... <html>
    ...     <head>
    ...         <meta name="tile-name" content="%(name)s" />
    ...     </head>
    ...     <body>
    ...         <p>
    ...             Non-ESI tile with query string %(queryString)s
    ...         </p>
    ...     </body>
    ... </html>""" % dict(name=self.id, queryString=self.request['QUERY_STRING'])

    >>> testTile2Type = TileType(
    ...     name=u'test.tile2',
    ...     title=u"Test tile 2",
    ...     description=u"A tile used for testing",
    ...     add_permission="cmf.ManagePortal",
    ...     view_permission="zope2.View")

    >>> class SimpleESITile(ESITile):
    ...     __name__ = 'test.tile3' # normally set by ZCML handler
    ...
    ...     def render(self):
    ...         return """\
    ... <html>
    ...     <head>
    ...         <meta name="tile-name" content="%(name)s" />
    ...     </head>
    ...     <body>
    ...         <p>
    ...             ESI tile with query string %(queryString)s
    ...         </p>
    ...     </body>
    ... </html>""" % dict(name=self.id, queryString=self.request['QUERY_STRING'])

    >>> testTile3Type = TileType(
    ...     name=u'test.tile3',
    ...     title=u"Test tile 3",
    ...     description=u"A tile used for testing",
    ...     add_permission="cmf.ManagePortal",
    ...     view_permission="zope2.View")

Register these in the same way that the ZCML handlers would, more or less.

.. code-block:: python

    >>> from Products.Five.security import protectClass
    >>> protectClass(NonESITile, 'zope2.View')
    >>> protectClass(SimpleESITile, 'zope2.View')

    >>> from App.class_init import InitializeClass
    >>> InitializeClass(NonESITile)
    >>> InitializeClass(SimpleESITile)

    >>> from zope.component import provideAdapter, provideUtility
    >>> from zope.interface import Interface
    >>> provideAdapter(NonESITile, (Interface, Interface,), Interface, u'test.tile2',)
    >>> provideUtility(testTile2Type, name=u'test.tile2')
    >>> provideAdapter(SimpleESITile, (Interface, Interface,), Interface, u'test.tile3',)
    >>> provideUtility(testTile3Type, name=u'test.tile3')

We will also register a simple layout and a simple page using these tiles.

.. code-block:: python

    >>> layoutHTML = u"""\
    ... <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    ... <html>
    ...     <head>
    ...         <title>Layout title</title>
    ...     </head>
    ...     <body>
    ...         <h1>Welcome!</h1>
    ...         <div data-panel="panel1">Content goes here</div>
    ...         <div id="layout-non-esi-tile" data-tile="./@@test.tile2/tile1">Layout tile 1 placeholder</div>
    ...         <div id="layout-esi-tile" data-tile="./@@test.tile3/tile2">Layout tile 2 placeholder</div>
    ...     </body>
    ... </html>
    ... """

To keep things simple, we'll skip the resource directory and layout indirection view,
instead just referencing a view containing the layout directly.

.. code-block:: python

    >>> from zope.publisher.browser import BrowserView
    >>> class Layout(BrowserView):
    ...     __name__ = 'test-layout'
    ...     def __call__(self):
    ...         return layoutHTML

    >>> protectClass(Layout, 'zope2.View')
    >>> InitializeClass(Layout)
    >>> provideAdapter(Layout, (Interface, Interface,), Interface, u'test-layout',)

    >>> pageHTML = u"""\
    ... <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    ... <html data-layout="./@@test-layout">
    ...     <body>
    ...         <div data-panel="panel1">
    ...             <div id="page-non-esi-tile" data-tile="./@@test.tile2/tile3?foo=bar">Page tile 3 placeholder</div>
    ...             <div id="page-esi-tile" data-tile="./@@test.tile3/tile4?foo=bar">Page tile 4 placeholder</div>
    ...         </div>
    ...     </body>
    ... </html>
    ... """

    >>> from zope.interface import implements
    >>> from plone.app.blocks.interfaces import IBlocksTransformEnabled
    >>> class Page(BrowserView):
    ...     implements(IBlocksTransformEnabled)
    ...     __name__ = 'test-page'
    ...     def __call__(self):
    ...         return pageHTML

    >>> protectClass(Page, 'zope2.View')
    >>> InitializeClass(Page)
    >>> provideAdapter(Page, (Interface, Interface,), Interface, u'test-page',)

ESI disabled
------------

We first render the page without enabling ESI.
The ESI-capable tiles should be rendered as normal.

.. code-block:: python

    >>> from plone.testing.z2 import Browser
    >>> app = layer['app']
    >>> browser = Browser(app)
    >>> browser.handleErrors = False

    >>> portal = layer['portal']
    >>> browser.open(portal.absolute_url() + '/@@test-page')

Some cleanup is needed to cover lxml platform discrepancies...

.. code-block:: python

    >>> print browser.contents.replace('<head><meta', '<head>\n\t<meta')
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=ASCII" />
        <title>Layout title</title>
        <meta name="tile-name" content="tile3" />
        <meta name="tile-name" content="tile4" />
        <meta name="tile-name" content="tile1" />
        <meta name="tile-name" content="tile2" />
        </head>
        <body>
            <h1>Welcome!</h1>
            <div data-panel="panel1">
            <p>
                Non-ESI tile with query string foo=bar
            </p>
            <p>
                ESI tile with query string foo=bar
            </p>
            </div>
            <p>
                Non-ESI tile with query string
            </p>
            <p>
                ESI tile with query string
            </p>
        </body>
    </html>
    <BLANKLINE>

ESI enabled
-----------

We can now enable ESI. This could be done using GenericSetup (with the
``registry.xml`` import step), or through the configuration registry
control panel. In code, it is done like so:

.. code-block:: python

    >>> from zope.component import getUtility
    >>> from plone.registry.interfaces import IRegistry
    >>> from plone.app.blocks.interfaces import IBlocksSettings
    >>> registry = getUtility(IRegistry)
    >>> registry.forInterface(IBlocksSettings).esi = True
    >>> import transaction
    >>> transaction.commit()

We can now perform the same rendering again. This time, the ESI-capable
tiles should be rendered as ESI links. See `plone.tiles`_ for more details.

.. code-block:: python

    >>> browser.open(portal.absolute_url() + '/@@test-page')
    >>> print browser.contents.replace('<head><meta', '<head>\n\t<meta')
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns:esi="http://www.edge-delivery.org/esi/1.0" xmlns="http://www.w3.org/1999/xhtml">
        <head>
        <meta http-equiv="Content-Type" content="text/html; charset=ASCII" />
        <title>Layout title</title>
        <meta name="tile-name" content="tile3" />
        <meta name="tile-name" content="tile1" />
        </head>
        <body>
            <h1>Welcome!</h1>
            <div data-panel="panel1">
            <p>
                Non-ESI tile with query string foo=bar
            </p>
            <esi:include src="http://nohost/plone/@@test.tile3/tile4/@@esi-body?foo=bar" />
            </div>
            <p>
                Non-ESI tile with query string
            </p>
            <esi:include src="http://nohost/plone/@@test.tile3/tile2/@@esi-body?" />
        </body>
    </html>
    <BLANKLINE>

When ESI rendering takes place, the following URLs will be called:

.. code-block:: python

    >>> browser.open("http://nohost/plone/@@test.tile3/tile4/@@esi-body?foo=bar")
    >>> print browser.contents
    <p>
        ESI tile with query string foo=bar
    </p>

    >>> browser.open("http://nohost/plone/@@test.tile3/tile2/@@esi-body?")
    >>> print browser.contents
    <p>
        ESI tile with query string
    </p>

.. _plone.tiles: http://pypi.python.org/pypi/plone.tiles
