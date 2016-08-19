Blocks rendering in detail
==========================

This doctest illustrates the blocks rendering process.
At a high level, it consists of the following steps:

0. Obtain the content page, an HTML document.
1. Look for a site layout link in the content page.

   This takes the form of an attribute on the html tag like ``<html data-layout="..." />``.

   Usually, the site layout URL will refer to a resource in a resource  directory of type ``sitelayout``,
   e.g. ``/++sitelayout++foo/site.html``,
   although the layout can be any URL.
   An absolute path like this will be adjusted so that it is always relative to the Plone site root.
2. Resolve and obtain the site layout.

   This is another HTML document.
3. Extract panels from the site layout.

   A panel is an element (usually a ``<div />``) in the layout page with a data-panel attribute,
   for example: ``<div data-panel="panel1" />``.
   The attribute specifies an id which *may* be used in the content page.
4. Merge panels.

   This is the process which applies the layout to the unstyled page.
   All panels in the layout page that have a matching element in the content page are replaced by the content page element.
   The rest of the content page is discarded.
5. Resolve and obtain tiles.

   A tile is a placeholder element in the page which will be replaced by the contents of a document referenced by a URL.

   A tile is identified by a placeholder element with a ``data-tile`` attribute containing the tile URL.

   Note that at this point, panel merging has taken place,
   so if a panel in the content page contains tiles, they will be carried over into the merge page.
   Also note that it is possible to have tiles outside of panels - the two concepts are not directly related.

   The ``plone.tiles`` package provides a framework for writing tiles,
   although in reality a tile can be any HTML page.
6. Place tiles into the page.

   The tile should resolve to a full HTML document.
   Any content found in the ``<head />`` of the tile content will be merged into the ``<head />`` of the rendered content.
   The contents of the ``<body />`` of the tile content are put into the rendered document at the tile placeholder.

Rendering step-by-step
----------------------

Let us now illustrate the rendering process.
We'll need a few variables defined first:

.. code-block:: python

    >>> from plone.testing.z2 import Browser
    >>> import transaction

    >>> app = layer['app']
    >>> portal = layer['portal']

    >>> browser = Browser(app)
    >>> browser.handleErrors = False

Creating a site layout
~~~~~~~~~~~~~~~~~~~~~~

The most common approach for managing site layouts is to use a resource registered using a ``plone.resource`` directory of type ``sitelayout``,
and then use the ``@@default-site-layout`` view to reference the content.
We will illustrate this below, but it is important to realise that ``plone.app.blocks`` works by post-processing responses rendered by Zope.
The content and layout pages could just as easily be created by views of content objects, or even resources external to Zope/Plone.

First, we will create a resource representing the site layout and its panels.
This includes some resources and other elements in the ``<head />``,
``<link />`` tags which identify tile placeholders and panels,
as well as content inside and outside panels.
The tiles in this case are managed by ``plone.tiles``, and are both of the same type.

.. code-block:: python

    >>> layoutHTML = """\
    ... <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    ... <html>
    ...     <head>
    ...         <title>Layout title</title>
    ...         <link rel="stylesheet" href="/layout/style.css" />
    ...         <script type="text/javascript">alert('layout');</script>
    ...
    ...         <style type="text/css">
    ...         div {
    ...             margin: 5px;
    ...             border: dotted black 1px;
    ...             padding: 5px;
    ...         }
    ...         </style>
    ...
    ...         <link rel="stylesheet" data-tile="./@@test.tile_nobody/tile_css" />
    ...     </head>
    ...     <body>
    ...         <h1>Welcome!</h1>
    ...         <div data-panel="panel1">Layout panel 1</div>
    ...         <div data-panel="panel2">
    ...             Layout panel 2
    ...             <div id="layout-tile1" data-tile="./@@test.tile1/tile1">Layout tile 1 placeholder</div>
    ...         </div>
    ...         <div data-panel="panel3">
    ...             Layout panel 3
    ...             <div id="layout-tile2" data-tile="./@@test.tile1/tile2">Layout tile 2 placeholder</div>
    ...         </div>
    ...     </body>
    ... </html>
    ... """

We can create an in-ZODB resource directory of type ``sitelayout`` that contains this layout.
Another way would be to register a resource directory in a package using ZCML, or use a global resource directory.
See ``plone.resource`` for more details.

.. code-block:: python

    >>> from Products.CMFCore.utils import getToolByName
    >>> from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
    >>> from StringIO import StringIO
    >>> from OFS.Image import File

    >>> resources = getToolByName(portal, 'portal_resources')
    >>> resources._setOb('sitelayout', BTreeFolder2('sitelayout'))
    >>> resources['sitelayout']._setOb('mylayout', BTreeFolder2('mylayout'))
    >>> resources['sitelayout']['mylayout']._setOb('site.html', File('site.html', 'site.html', StringIO(layoutHTML)))

    >>> transaction.commit()

This resource can now be accessed using the path ``/++sitelayout++mylayout/site.html``.
Let's render it on its own to verify that.

.. code-block:: python

    >>> browser.open(portal.absolute_url() + '/++sitelayout++mylayout/site.html')
    >>> print browser.contents
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html>
        <head>
            <title>Layout title</title>
            <link rel="stylesheet" href="/layout/style.css" />
            <script type="text/javascript">alert('layout');</script>
    <BLANKLINE>
            <style type="text/css">
            div {
                margin: 5px;
                border: dotted black 1px;
                padding: 5px;
            }
            </style>
    <BLANKLINE>
            <link rel="stylesheet" data-tile="./@@test.tile_nobody/tile_css" />
        </head>
        <body>
            <h1>Welcome!</h1>
            <div data-panel="panel1">Layout panel 1</div>
            <div data-panel="panel2">
                Layout panel 2
                <div id="layout-tile1" data-tile="./@@test.tile1/tile1">Layout tile 1 placeholder</div>
            </div>
            <div data-panel="panel3">
                Layout panel 3
                <div id="layout-tile2" data-tile="./@@test.tile1/tile2">Layout tile 2 placeholder</div>
            </div>
        </body>
    </html>

We can now set this as the site-wide default layout by setting the registry key ``plone.defaultSiteLayout``.
There are two indirection views, ``@@default-site-layout`` and ``@@page-site-layout``, that respect this registry setting.
By using one of these views to reference the layout of a given page, we can manage the default site layout centrally.

.. code-block:: python

    >>> from zope.component import getUtility
    >>> from plone.registry.interfaces import IRegistry
    >>> registry = getUtility(IRegistry)
    >>> registry['plone.defaultSiteLayout'] = '/++sitelayout++mylayout/site.html'
    >>> transaction.commit()

Creating a page layout and tiles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Next, we will define the markup of a content page that uses this layout via the ``@@default-site-layout`` indirection view:

.. code-block:: python

    >>> pageHTML = """\
    ... <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    ... <html data-layout="./@@default-site-layout">
    ...     <body>
    ...         <h1>Welcome!</h1>
    ...         <div data-panel="panel1">
    ...             Page panel 1
    ...             <div id="page-tile2" data-tile="./@@test.tile1/tile2?magicNumber:int=2">Page tile 2 placeholder</div>
    ...         </div>
    ...         <div data-panel="panel2">
    ...             Page panel 2
    ...             <div id="page-tile3" data-tile="./@@test.tile1/tile3">Page tile 3 placeholder</div>
    ...         </div>
    ...         <div data-panel="panel4">
    ...             Page panel 4 (ignored)
    ...             <div id="page-tile4" data-tile="./@@test.tile1/tile4">Page tile 4 placeholder</div>
    ...         </div>
    ...     </body>
    ... </html>
    ... """

We then register a view that simply return this HTML,
and a tile type which we can use to test tile rendering.

We do this in code for the purposes of the test,
and we have to apply security because we will shortly render those pages using the test publisher.
In real life, these could be registered using the standard ``<browser:page />`` and ``<plone:tile />`` directives.

.. code-block:: python

    >>> from zope.publisher.browser import BrowserView
    >>> from zope.interface import Interface, implements
    >>> from zope import schema
    >>> from plone.tiles import Tile
    >>> from plone.app.blocks.interfaces import IBlocksTransformEnabled

    >>> class Page(BrowserView):
    ...     implements(IBlocksTransformEnabled)
    ...     __name__ = 'test-page'
    ...     def __call__(self):
    ...         return pageHTML

    >>> class ITestTile(Interface):
    ...     magicNumber = schema.Int(title=u"Magic number", required=False)

    >>> class TestTile(Tile):
    ...     __name__ = 'test.tile1' # normally set by ZCML handler
    ...
    ...     def __call__(self):
    ...         # fake a page template to keep things simple in the test
    ...         return """\
    ... <html>
    ...     <head>
    ...         <meta name="tile-name" content="%(name)s" />
    ...     </head>
    ...     <body>
    ...         <p>
    ...             This is a demo tile with id %(name)s
    ...         </p>
    ...         <p>
    ...             Magic number: %(number)d; Form: %(form)s; Query string: %(queryString)s; URL: %(url)s
    ...         </p>
    ...     </body>
    ... </html>""" % dict(name=self.id, number=self.data['magicNumber'] or -1,
    ...                   form=sorted(self.request.form.items()), queryString=self.request['QUERY_STRING'], url=self.request.getURL())

Let's add another tile, this time only a head part.
This could for example be a tile that only needs to insert some CSS.

.. code-block:: python

    >>> class TestTileNoBody(Tile):
    ...     __name__ = 'test.tile_nobody'
    ...
    ...     def __call__(self):
    ...         return """\
    ... <html>
    ...     <head>
    ...         <link rel="stylesheet" type="text/css" href="tiled.css" />
    ...     </head>
    ... </html>"""

We register these views and tiles in the same way the ZCML handlers for ``<browser:page />`` and ``<plone:tile />`` would:

.. code-block:: python

    >>> from plone.tiles.type import TileType
    >>> from Products.Five.security import protectClass
    >>> from App.class_init import InitializeClass
    >>> from zope.component import provideAdapter, provideUtility
    >>> from zope.interface import Interface

    >>> testTileType = TileType(
    ...     name=u'test.tile1',
    ...     title=u"Test tile",
    ...     description=u"A tile used for testing",
    ...     add_permission="cmf.ManagePortal",
    ...     view_permission="zope2.View",
    ...     schema=ITestTile)

    >>> testTileTypeNoBody = TileType(
    ...     name=u'test.tile_nobody',
    ...     title=u"Test tile using only a header",
    ...     description=u"Another tile used for testing",
    ...     add_permission="cmf.ManagePortal",
    ...     view_permission="zope2.View")

    >>> protectClass(Page, 'zope2.View')
    >>> protectClass(TestTile, 'zope2.View')

    >>> InitializeClass(Page)
    >>> InitializeClass(TestTile)

    >>> provideAdapter(Page, (Interface, Interface,), Interface, u'test-page')
    >>> provideAdapter(TestTile, (Interface, Interface,), Interface, u'test.tile1',)
    >>> provideAdapter(TestTileNoBody, (Interface, Interface,), Interface, u'test.tile_nobody',)
    >>> provideUtility(testTileType, name=u'test.tile1')
    >>> provideUtility(testTileTypeNoBody, name=u'test.tile_nobody')

Rendering the page
~~~~~~~~~~~~~~~~~~

We can now render the page.
Provided ``plone.app.blocks`` is installed and working, it should perform its magic.
We make sure that Zope is in "development mode" to get pretty-printed output.

.. code-block:: python

    >>> browser.open(portal.absolute_url() + '/@@test-page')
    >>> print browser.contents.replace('<head><meta', '<head>\n\t<meta')
    <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
    <html xmlns="http://www.w3.org/1999/xhtml">
      <head>
        <meta http-equiv="Content-Type" content="text/html; charset=ASCII" />
        <title>Layout title</title>
        <link rel="stylesheet" href="/layout/style.css" />
        <script type="text/javascript">alert('layout');</script>
        <style type="text/css">
            div {
                margin: 5px;
                border: dotted black 1px;
                padding: 5px;
            }
            </style>
        <link rel="stylesheet" type="text/css" href="tiled.css" />
        <meta name="tile-name" content="tile2" />
        <meta name="tile-name" content="tile3" />
        <meta name="tile-name" content="tile2" />
      </head>
      <body>
            <h1>Welcome!</h1>
            <div data-panel="panel1">
                Page panel 1
            <p>
                This is a demo tile with id tile2
            </p>
            <p>
                Magic number: 2; Form: [('magicNumber', 2)]; Query string: magicNumber:int=2; URL: http://nohost/plone/@@test.tile1/tile2
            </p>
            </div>
            <div data-panel="panel2">
                Page panel 2
            <p>
                This is a demo tile with id tile3
            </p>
            <p>
                Magic number: -1; Form: []; Query string: ; URL: http://nohost/plone/@@test.tile1/tile3
            </p>
            </div>
            <div data-panel="panel3">
                Layout panel 3
            <p>
                This is a demo tile with id tile2
            </p>
            <p>
                Magic number: -1; Form: []; Query string: ; URL: http://nohost/plone/@@test.tile1/tile2
            </p>
            </div>
        </body>
    </html>
    <BLANKLINE>

Notice how:

* Panels from the page have been merged into the layout, replacing the corresponding panels there.
* The ``<head />`` sections of the two documents have been merged
* The rest of the layout page is intact
* The rest of the content page is discarded
* The tiles have been rendered, replacing the relevant placeholders
* The ``<head />`` section from the rendered tiles has been merged into the ``<head />`` of the output page.

Using VHM
~~~~~~~~~

Make sure to have a clean browser:

.. code-block:: python

    >>> browser = Browser(app)
    >>> browser.handleErrors = False

Using Virtual Host Monster we rewrite the url to consider all content being under ``/``:

.. code-block:: python

    >>> vhm_url = 'http://nohost/VirtualHostBase/http/nohost:80/plone/VirtualHostRoot/'
    >>> browser.open(vhm_url + '/@@test-page')

Tiles should return an url according to this:

.. code-block:: python

    >>> 'Magic number: -1; Form: []; Query string: ; URL: http://nohost/@@test.tile1/tile2' in browser.contents
    True

Now we deal with _vh_* arguments. We expect our site to be under a subdir with id *subplone*:

.. code-block:: python

    >>> vhm_url = 'http://nohost/VirtualHostBase/http/nohost:80/plone/VirtualHostRoot/_vh_subplone'
    >>> browser.open(vhm_url + '/@@test-page')

Tiles should return an url according to this:

.. code-block:: python

    >>> 'Magic number: -1; Form: []; Query string: ; URL: http://nohost/subplone/@@test.tile1/tile2' in browser.contents
    True

