Introduction
============

This package implements the 'blocks' rendering model, by providing several
transform stages that hook into ``plone.transformchain``.

The stages are:

 plone.app.blocks.parsexml (order 8000)
    Turns the response in a ``repoze.xmliter`` ``XMLSerializer`` object.
    This is then used by the subsequent stages. If the input is not HTML,
    the transformation is aborted.

 plone.app.blocks.mergepanels (order 8100)
    Looks up the site layout and executes the panel merge algorithm. Sets a
    request variable ('plone.app.blocks.merged') to indicate that it has
    done its job.

 plone.app.blocks.tiles (order 8500)
    Resolve tiles and place them directly into the merged layout. This is the
    fallback for views that do not opt into ITilePageRendered.

 plone.app.blocks.esirender (order 8900)
    Only executed if the request key ``plone.app.blocks.esi`` is set and
    has a true value, as would be the case if any ESI-rendered tiles are
    included and ESI rendering is enabled globally. This step will serialise
    the response down to a string and perform some substitution to make ESI
    rendering work.

The package also registers the ``sitelayout`` ``plone.resource`` resource
type, allowing site layouts to be created easily as static HTML files served
from resource directories. The URL to a site layout is typically something
like::

    /++sitelayout++my.layout/site.html

See ``plone.resource`` for more information about how to register resource
directories. For site layouts, the ``type`` of the resource directory is
``sitelayout``.

It is possible to provide a manifest file that gives a title, description and
alternative default file for a site layout HTML file in a resource directory.
To create such a manifest, put a ``manifest.cfg`` file in the layout directory
with the following structure::

    [sitelayout]
    title = My layout title
    description = Some description
    file = some-html-file.html

All keys are optional. The file defaults to ``site.html``.

A vocabulary factory called ``plone.availableSiteLayouts`` is registered to
allow lookup of all registered site layouts.  The terms in this vocabulary
use the URL as a value, the resource directory name as a token, and the 
title from the manifest (falling back on a sanitised version of the resource
directory name) as the title.

The current default site layout can be identified by the ``plone.registry``
key ``plone.defaultSiteLayout``, which is set to ``None`` by default. To
always use the current site default, use::

    <html data-layout="./@@default-site-layout">

The ``@@default-site-layout`` view will render the current default site
layout.

It is possible for the default site layout to be overridden per section,
by having parent objects provide or be adaptable to
``plone.app.blocks.layoutbehavior.ILayoutAware``. As the module name implies,
this interface can be used as a ``plone.behavior`` behavior, but it can also
be implemented directly or used as a standard adapter.

The ``ILayoutAware`` interface defines three properties:

* ``content``, which contains the body of the page to be rendered
* ``pageSiteLayout``, which contains the path to the site layout to be used
  for the given page. It can be ``None`` if the default is to be used.
* ``sectionSiteLayout``, which contains the path to the site layout to be
  used for pages *underneath* the given page (but not for the page itself).
  Again, it can be ``None`` if the default is to be used.

To make use of the page site layout, use the following:

    <html data-layout="./@@default-site-layout">

See ``rendering.txt`` for detailed examples of how the processing is applied,
and ``esi.txt`` for details about how Edge Side Includes can be supported.
