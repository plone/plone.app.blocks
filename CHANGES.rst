Changelog
=========

4.0.2 (2017-01-03)
------------------

Fixes:

- Fix issue where error in diazo transform for a single tile aborted tile
  merge as whole
  [datakurre]


4.0.1 (2016-12-28)
------------------

Fixes:

- Fix issue where tile data storage decoded HTML primary fields
  using ASCII instead of utf-8 causing broken broken latin
  characters in attribute values
  [datakurre]


4.0.0 (2016-12-13)
------------------

Incompatibilities:

- Remove grid transform, because it did not serve its purpose as as well
  expected and required HTML-syntax not editable by humans; Instead using
  grid framework agnostic CSS class names and building CSS grid against
  those class names is recommended
  [agitator]

- Remove ``IOmittedField`` marker from layout behavior fields not meant to be
  displayed on legacy Deco UIs
  [jensens]

- Rename ``ILayoutAware.content`` to ``ILayoutAware.customContentLayout``
  [datakurre]

- Move functions ``getDefaultAjaxLayout``, ``getDefaultSiteLayout``,
  ``getLayout`` and ``getLayoutAwareSiteLayout`` to ``.layoutbehavior`` in
  order to avoid circular imports (all deprecated now, see section New).
  [jensens]

- Move views from ``.layoutbehavior`` to new module ``.layoutviews`` in order
  to avoid circular imports.  Deprecated deferred imports are in place.
  [jensens]

New:

- Add ``ILayoutAware.content`` as layout independent "layout like" tile
  configuration and data storage for all serializable tile configurations
  [datakurre]

- Add ``@@layout_preview`` view for previewing currently drafted layout aware
  content
  [datakurre]

- ``ILayoutAware`` is now also responsible to lookup the behaviors.
  [jensens]

- Get layouts always by adapting with ``ILayoutAware``.  This introduces a
  generic adapter and a behavior adapter.  Deprecated the formerly used functions
  ``getLayout`` ``getDefaultSiteLayout`` just calls
  ``ILayoutAware().site_layout`` and is deprected.  ``getLayout`` just calls
  ``ILayoutAware().content_layout`` and is deprecated.
  [jensens]

- Behavior shortname ``plone.layoutaware`` added.
  [jensens]

Fixes:

- Handle missing content layouts so they do not cause an error
  [vangheem]

- A tile raising an 401 Unauthorized on traversal,
  results in a status rewriting to a 302 which results in 200 login form.
  The whole login form page then is rendered as the tile contents.
  This patch catches the 401 by providing a custom exception handler.
  The 401 is catched and ignored. This is not pefect yet and need some work,
  but it at least does not break design and intended behavior of tiles.
  [jensens]

Refactoring:

- Housekeeping: ZCA decorators, sorted imports, line-lengths and related.
  [jensens]

- Reformat documentation.
  [gforcada]

- Update travis configuration.
  [gforcada]


3.1.0 (2016-03-28)
------------------

New:

- Don't make a tile exception break other tiles (closes `#27`_).
  [rodfersou, datakurre]

- Provide new getLayoutsFromDirectory utility to get layouts from any
  plone.resource directory, not just the base resource directory
  [vangheem]

- Index layout data; When collective.dexteritytextindexer is present,
  its *Dynamic SearchableText indexer behavior* must be enabled for content
  type
  [vangheem, datakurre]

- Cleanup tile data on save/edit
  [vangheem]


3.0.1 (2015-09-23)
------------------

- Remove the default 'Custom layout' display menu registration for
  'layout_view', because it was not possible to customize it with more exact
  registration
  [datakurre]

- Fix the default view to report template name as 'template-layout'
  [datakurre]


3.0.0 (2015-09-16)
------------------

- Change layout behavior default view name from ``view`` to ``layout_view``
  [datakurre]

- Add to be able to set default grid system in registry settings
  [vangheem]

- Add support for provide more than one layout with a layout directory
  and manifest (replaces removed layout variants)
  [vangheem]

- Add ``contentlayout`` resource type with ``plone.availableContentLayouts``
  vocabulary and ``++contentlayout++`` traverser
  [vangheem]

- Add ``contentLayout`` field to layoutbehavior to select the rendered layout
  from centrally managed content layouts
  [vangheem]

- Add content type specific registry configuration with key
  ``plone.app.blocks.default_layout.portal_type`` for used default content
  layout when custom layout is not defined
  [vangheem]

- Add to check ``plone.app.blocks.default_layout`` registry key for a default
  content layout path when content type specific default content layout path is
  not set
  [datakurre]

- Fixed layout behavior to apply Plone outputfilters for rendered content
  [datakurre]

- Add default grid system registry setting
  [vangheem]

- Restore support for Plone 4.2.x
  [datakurre]

- Remove layout variants introduced in 2.0.0, in favor of ability to
  provide more than one layout with a layout directory and manifest by
  using multiple ``[...layout]`` directive in the same manifest
  [vangheem]


2.1.2 (2015-06-10)
------------------

- Fix issue where grid transform did replaced class names instead of appending
  to them
  [datakurre]


2.1.1 (2015-06-10)
------------------

- Fix BS3 grid transform to only introduce offset when the tile position is
  greater than the current position in the current row
  [datakurre]

- Fix issue where tiles with empty response or syntax error broke tiles
  transform (add to log syntax errors instead)
  [datakurre]


2.1.0 (2015-05-25)
------------------

- Add support for indexing layout field into SearchableText index when
  collective.dexteritytextindexer is installed and its Dynamic SearchableText
  indexer behavior is enabled for the indexed content type with Layout support
  behavior
  [datakurre]


2.0.0 (2015-04-21)
------------------

- Fix package dependencies; remove dependency on unittest2.
  [hvelarde]

- Change blocks transforms to be opt-in for only published objects e.g. views
  or requests with IBlocksTransformEnabled (marker) interface [fixes #11]
  [datakurre]

- Change tags with data-tiles-attrs to be completely replaced (by
  replace_with_children instad of replace_content) to restore original
  design and support for site layout tiles in HTML document head tag
  [datakurre]

- Change default site layout to be optional by adding an implicit
  main_template-based site layout when the default site layout is not set
  [datakurre]

- Change to retry resolveResources with 301 or 302 response when redirect
  location is for the same site
  [datakurre]

- Add support for AJAX site layout for requests with ``ajax_load`` parameter
  either by getting a layout from a reqistry key ``plone.defaultAjaxLayout``
  or by using an implicit main_template-based AJAX layout
  [simahawk, datakurre]

- Add extensible CSS grid transform with built-in transforms for Deco
  and Bootstrap 3 grid systems
  [bloodbare, ACatila]

  .. code:: xml

     <utility
         provides=".gridsystem.IGridSystem"
         component=".gridsystem.DecoGridSystem"
         name="deco"
         />

  .. code:: html

     <html data-gridsystem="deco">
       ...
       <div data-grid='{"type": "row"}'>
         <div data-grid='{"type": "cell",
                          "info": {"xs": "false",
                                   "sm": "False",
                                   "lg": "True",
                          "pos": {"x":1,
                                  "width": 12}}}'>
          </div>
       </div>
     </html>

  .. code:: html

     <div class="row">
        <div class="cell position-1 width-12">
        </div>
     </div>

- Add default view for ILayoutAware content and register a localizable display
  menu item called *Custom layout* for it when *plone.app.contentmenu* is
  present
  [datakurre]

- Add Layout-fieldset for ILayoutAware behavior
  [datakurre]

- Add support to use the whole tile as its body when both head and body tags
  are missing (add support for using Dexterithy display widgets as tiles)
  [datakurre]

- Add support for layout variants (for supporting multiple layouts in a single
  resource folder)
  [datakurre]

  .. code:: ini

     [sitelayout]
     ...

     [sitelayout:variants]
     document_layout = document.html

- Add experimental support for tile-specific Diazo-rules
  with data-attribute ``data-rules="/++sitelayout++name/rules.xml"``.
  [datakurre]

- Fix issue with tile without body-tag breaking the tile composition (fixes
  issues with some p.a.standardtiles returning only <html/> in some conditions)
  [datakurre]

- Fix issue where <![CDATA[...]]> block was quoted (and therefore broken) by
  lxml serializer
  [datakurre]

- Fix issue where XML parser dropped head for layout with CRLF-endings
  [datakurre]

- Fix plone.app.blocks re-install to not reset existing plone.defaultSiteLayout
  and plone.defaultAjaxLayout settings (by setting the values in a custom
  setuphandler)
  [datakurre]

- Fix and update tests, PEP8
  [gyst, datakurre, gforcada]

- Fix to set the merging request flag before testing the merge results to allow
  staticly placed tiles in content templates to be rendered properly.
  [cewing]

- Solve issue with VHM and tile rendering. Fixes
  https://dev.plone.org/ticket/13581 [ericof]

- Add z3c.autoinclude support
  [cdw9, calvinhp]


1.1 (2012-12-17)
----------------

- make sure to use correct url of tile
  [vangheem]

- handle not found errors while rendering tiles so layout
  isn't borked
  [vangheem]


1.0 (2012-06-23)
----------------

- initial release.
  [garbas]

.. _`#27`: https://github.com/plone/plone.app.blocks/issues/27
