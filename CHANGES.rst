Changelog
=========

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
