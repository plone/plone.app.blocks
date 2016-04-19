# -*- coding: utf-8 -*-
from plone.app.blocks.testing import BLOCKS_FIXTURE
from plone.app.blocks.tiles import renderTiles
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.tiles import Tile
from repoze.xmliter.utils import getHTMLSerializer
from zope import schema
from zope.configuration import xmlconfig
from zope.interface import implementer
from zope.interface import Interface

import unittest


class ITestTile(Interface):

    magicNumber = schema.Int(title=u"Magic number", required=False)


@implementer(ITestTile)
class TestTile(Tile):

    def __call__(self):
        # fake a page template to keep things simple in the test
        return """\
<html>
<head>
  <meta name="tile-name" content="%(name)s" />
</head>
<body>
  <p>
    This is a demo tile with id %(name)s
  </p>
  <p>
    Magic number: %(number)d; Form: %(form)s;
    Query string: %(queryString)s; URL: %(url)s
  </p>
</body>
</html>""" % dict(name=self.id, number=self.data['magicNumber'] or -1,
                  form=sorted(self.request.form.items()),
                  queryString=self.request['QUERY_STRING'],
                  url=self.request.getURL())


@implementer(ITestTile)
class TestTileBroken(TestTile):

    def __call__(self):
        raise Exception("This tile is broken.")


class TestTilesLayer(PloneSandboxLayer):

    defaultBases = (BLOCKS_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        xmlconfig.string("""\
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:plone="http://namespaces.plone.org/plone"
    i18n_domain="plone.app.blocks">

  <include package="plone.tiles" file="meta.zcml" />

  <plone:tile
      name="test.tile1"
      title="Test Tile"
      description=""
      add_permission="cmf.ModifyPortalContent"
      schema="plone.app.blocks.tests.test_tiles.ITestTile"
      class="plone.app.blocks.tests.test_tiles.TestTile"
      permission="zope2.View"
      for="*"
      />

  <plone:tile
      name="test.tile1.broken"
      title="Broken Test Tile"
      description=""
      add_permission="cmf.ModifyPortalContent"
      schema="plone.app.blocks.tests.test_tiles.ITestTile"
      class="plone.app.blocks.tests.test_tiles.TestTileBroken"
      permission="zope2.View"
      for="*"
      />

</configure>
""", context=configurationContext)

BLOCKS_TILES_FIXTURE = TestTilesLayer()

BLOCKS_TILES_INTEGRATION_TESTING = IntegrationTesting(
    bases=(BLOCKS_TILES_FIXTURE,), name="Blocks:Tiles:Integration")


testLayout1 = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html data-layout="./@@default-site-layout">
<head></head>
<body>
  <h1>Welcome!</h1>
  <div data-panel="panel1">
    Page panel 1
    <div id="page-tile2" data-tile="./@@test.tile1/tile2?magicNumber:int=2">Page tile 2 placeholder</div>
  </div>
  <div data-panel="panel2">
    Page panel 2
    <div id="page-tile3" data-tile="./@@test.tile1/tile3">Page tile 3 placeholder</div>
  </div>
  <div data-panel="panel4">
    Page panel 4 (ignored)
    <div id="page-tile4" data-tile="./@@test.tile1/tile4">Page tile 4 placeholder</div>
  </div>
</body>
</html>
"""


testLayout2 = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html data-layout="./@@default-site-layout">
<head></head>
<body>
  <h1>Welcome!</h1>
  <div data-panel="panel1">
    Page panel 1
    <div id="page-tile2" data-tile="./@@test.tile1/tile2?magicNumber:int=2">Page tile 2 placeholder</div>
  </div>
  <div data-panel="panel2">
    Page panel 2
    <div id="page-tile3" data-tile="./@@test.tile1.broken/tile3">Page tile 3 placeholder</div>
  </div>
  <div data-panel="panel4">
    Page panel 4 (ignored)
    <div id="page-tile4" data-tile="./@@test.tile1/tile4">Page tile 4 placeholder</div>
  </div>
</body>
</html>
"""


class TestRenderTiles(unittest.TestCase):

    layer = BLOCKS_TILES_INTEGRATION_TESTING

    def testRenderTiles(self):
        serializer = getHTMLSerializer([testLayout1])
        request = self.layer['request']
        tree = serializer.tree
        renderTiles(request, tree)
        result = serializer.serialize()
        self.assertIn('This is a demo tile with id tile2', result)
        self.assertIn('This is a demo tile with id tile3', result)
        self.assertIn('This is a demo tile with id tile4', result)

    def testRenderTilesError(self):
        serializer = getHTMLSerializer([testLayout2])
        request = self.layer['request']
        tree = serializer.tree
        renderTiles(request, tree)
        result = serializer.serialize()
        self.assertIn('This is a demo tile with id tile2', result)
        self.assertNotIn('This is a demo tile with id tile3', result)
        self.assertIn('There was an error while rendering this tile', result)
        self.assertIn('This is a demo tile with id tile4', result)
