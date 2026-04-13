"""Benchmark: Performance comparison with and without per-request caching.

Run with: bin/test -s plone.app.blocks -t benchmark -v

This is not a regular unit test — it measures timing to visualize
the performance impact of the caching changes.
"""

from plone.app.blocks.layoutbehavior import ILayoutAware
from plone.app.blocks.layoutbehavior import ILayoutBehaviorAdaptable
from plone.app.blocks.layoutbehavior import LAYOUT_STORAGE_CACHE_KEY
from plone.app.blocks.layoutbehavior import LayoutAwareTileDataStorage
from plone.app.blocks.testing import BLOCKS_FIXTURE
from plone.app.blocks.tiles import renderTiles
from plone.app.blocks.utils import TILE_RESOLVE_CACHE_KEY
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.fti import DexterityFTI
from plone.registry.interfaces import IRegistry
from plone.resource.utils import queryResourceDirectory
from plone.tiles import Tile
from plone.tiles.interfaces import ITileType
from plone.tiles.type import TileType
from repoze.xmliter.utils import getHTMLSerializer
from zope import schema
from zope.component import getUtility
from zope.component import provideUtility
from zope.configuration import xmlconfig
from zope.interface import implementer
from zope.interface import Interface

import statistics
import sys
import time
import unittest


class ITestTile(Interface):
    magicNumber = schema.Int(title="Magic number", required=False)


@implementer(ITestTile)
class BenchTile(Tile):
    def __call__(self):
        return """\
<html>
<head><meta name="tile-name" content="{}" /></head>
<body><p>Tile {} rendered</p></body>
</html>""".format(self.id, self.id)


class BenchTileWithSubtile(Tile):
    def __call__(self):
        return """\
<html>
<body>
  <p>Parent tile</p>
  <div data-tile="./@@bench.tile/subtile"/>
</body>
</html>"""


class BenchmarkLayer(PloneSandboxLayer):
    defaultBases = (BLOCKS_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        xmlconfig.string(
            """\
<configure
    xmlns="http://namespaces.zope.org/zope"
    xmlns:plone="http://namespaces.plone.org/plone"
    i18n_domain="plone.app.blocks">

  <include package="plone.tiles" file="meta.zcml" />

  <plone:tile
      name="bench.tile"
      title="Bench Tile"
      add_permission="cmf.ModifyPortalContent"
      schema="plone.app.blocks.tests.test_benchmark_cache.ITestTile"
      class="plone.app.blocks.tests.test_benchmark_cache.BenchTile"
      permission="zope2.View"
      for="*"
      />

  <plone:tile
      name="bench.subtile"
      title="Bench Subtile"
      add_permission="cmf.ModifyPortalContent"
      class="plone.app.blocks.tests.test_benchmark_cache.BenchTileWithSubtile"
      permission="zope2.View"
      for="*"
      />

</configure>
""",
            context=configurationContext,
        )


BENCHMARK_FIXTURE = BenchmarkLayer()
BENCHMARK_INTEGRATION_TESTING = IntegrationTesting(
    bases=(BENCHMARK_FIXTURE,), name="Blocks:Benchmark:Integration"
)


def _generate_layout(num_tiles, use_subtiles=False):
    """Generate an HTML layout with the given number of tiles."""
    tile_name = "bench.subtile" if use_subtiles else "bench.tile"
    tiles_html = "\n".join(
        f'    <div data-tile="./@@{tile_name}/tile{i}?magicNumber:int={i}"></div>'
        for i in range(num_tiles)
    )
    return f"""\
<!DOCTYPE html>
<html>
<head></head>
<body>
  <h1>Benchmark Layout</h1>
{tiles_html}
</body>
</html>
"""


def _measure(func, iterations=20):
    """Measure execution time over multiple iterations, return (mean, stdev, times)."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = (time.perf_counter() - start) * 1000  # ms
        times.append(elapsed)
    return (
        statistics.mean(times),
        statistics.stdev(times) if len(times) > 1 else 0,
        times,
    )


def _bar(value, max_value, width=40):
    """Create an ASCII bar."""
    filled = int(round(value / max_value * width)) if max_value > 0 else 0
    filled = min(filled, width)
    return "█" * filled + "░" * (width - filled)


class TestBenchmarkTileRendering(unittest.TestCase):
    layer = BENCHMARK_INTEGRATION_TESTING

    def _render_tiles(self, layout_html, clear_cache=False):
        """Render tiles from the given layout HTML."""
        request = self.layer["request"]
        if clear_cache:
            request.environ.pop(TILE_RESOLVE_CACHE_KEY, None)
        serializer = getHTMLSerializer([layout_html])
        renderTiles(request, serializer.tree)
        return str(serializer)

    def test_benchmark_tile_rendering(self):
        """Benchmark: tile rendering with and without per-request cache.

        Measures the benefit of caching when the same tile URL is referenced
        multiple times in a single page (common with shared header/footer tiles).
        """
        request = self.layer["request"]
        iterations = 20

        print("\n")
        print("=" * 78)
        print("  BENCHMARK: Tile Rendering — Per-Request Subrequest Cache")
        print("=" * 78)
        print()
        print(f"  Layout: N unique tiles + N duplicate references = 2N total")
        print(f"  Iterations per measurement: {iterations}")
        print()
        print(
            f"  {'Tiles':>6}  {'No Cache (ms)':>14}  {'With Cache (ms)':>16}  "
            f"{'Speedup':>8}  Chart"
        )
        print(f"  {'─' * 6}  {'─' * 14}  {'─' * 16}  {'─' * 8}  {'─' * 40}")

        # Warmup
        layout_warmup = _generate_layout(2)
        for _ in range(3):
            request.environ.pop(TILE_RESOLVE_CACHE_KEY, None)
            serializer = getHTMLSerializer([layout_warmup])
            renderTiles(request, serializer.tree)

        tile_counts = [3, 6, 10, 15]

        for num_tiles in tile_counts:
            layout_dupes = _generate_layout_with_duplicates(num_tiles)

            # WITHOUT cache: patch resolveResource to skip cache
            from plone.app.blocks import utils as utils_mod

            _original_resolveResource = utils_mod.resolveResource

            def resolveResource_no_cache(url):
                """Bypass per-request cache to simulate old behavior."""
                from urllib import parse as urlparse

                url = urlparse.unquote(url)
                scheme, netloc, path, params, query, fragment = urlparse.urlparse(url)
                if path.count("++") == 2:
                    _, resource_type, path = path.split("++")
                    resource_name, _, path = path.partition("/")
                    directory = queryResourceDirectory(resource_type, resource_name)
                    if directory:
                        try:
                            res = directory.readFile(path)
                            if isinstance(res, bytes):
                                res = res.decode()
                            return res
                        except Exception:
                            pass
                if url.startswith("/"):
                    from zope.component.hooks import getSite

                    site = getSite()
                    url = "/".join(site.getPhysicalPath()) + url
                from plone.subrequest import subrequest

                response = subrequest(url)
                resolved = response.getBody()
                if isinstance(resolved, bytes):
                    resolved = resolved.decode("utf-8")
                return resolved

            def run_no_cache():
                utils_mod.resolveResource = resolveResource_no_cache
                try:
                    request.environ.pop(TILE_RESOLVE_CACHE_KEY, None)
                    serializer = getHTMLSerializer([layout_dupes])
                    renderTiles(request, serializer.tree)
                finally:
                    utils_mod.resolveResource = _original_resolveResource

            def run_with_cache():
                request.environ.pop(TILE_RESOLVE_CACHE_KEY, None)
                serializer = getHTMLSerializer([layout_dupes])
                renderTiles(request, serializer.tree)

            mean_no_cache, std_no_cache, _ = _measure(run_no_cache, iterations)
            mean_cached, std_cached, _ = _measure(run_with_cache, iterations)

            speedup = mean_no_cache / mean_cached if mean_cached > 0 else 1.0
            max_val = max(mean_no_cache, mean_cached)
            bar_no = _bar(mean_no_cache, max_val, 20)
            bar_ca = _bar(mean_cached, max_val, 20)

            print(
                f"  {num_tiles * 2:>6}  {mean_no_cache:>11.2f} ms  {mean_cached:>13.2f} ms  "
                f"{speedup:>6.2f}x  {bar_no} no cache"
            )
            print(f"  {'':>6}  {'':>14}  {'':>16}  {'':>8}  {bar_ca} cached")

        print()
        print("=" * 78)
        print()

    def test_benchmark_storage_parsing(self):
        """Benchmark: LayoutAwareTileDataStorage HTML parsing cache.

        Shows the benefit of caching the parsed HTML storage per request.
        """
        portal = self.layer["portal"]
        request = self.layer["request"]

        setRoles(portal, TEST_USER_ID, ("Manager",))
        fti = DexterityFTI(
            "BenchDoc",
            global_allow=True,
            behaviors=(
                "plone.app.dexterity.behaviors.metadata.IBasic",
                "plone.app.blocks.layoutbehavior.ILayoutAware",
            ),
        )
        portal.portal_types._setObject("BenchDoc", fti)
        portal.invokeFactory("BenchDoc", "bench-doc", title="Bench Doc")
        setRoles(portal, TEST_USER_ID, ("Member",))

        context = portal["bench-doc"]

        # Create content with multiple tiles
        tile_type = TileType(
            name="bench.storage.tile",
            title="Bench Storage Tile",
            add_permission="cmf.ModifyPortalContent",
            view_permission="zope2.View",
            schema=ITestTile,
        )
        provideUtility(tile_type, provides=ITileType, name="bench.storage.tile")

        num_tiles = 10
        tile_divs = "\n".join(
            f'<div data-tile="@@bench.storage.tile/tile{i}" '
            f"data-tiledata='{{\"magicNumber\": {i}}}' />"
            for i in range(num_tiles)
        )
        ILayoutAware(context).content = f"""\
<html>
<body>
{tile_divs}
</body>
</html>
"""

        iterations = 30
        accesses_per_iteration = num_tiles

        print("\n")
        print("=" * 78)
        print("  BENCHMARK: LayoutAwareTileDataStorage — HTML Parsing Cache")
        print("=" * 78)
        print()
        print(f"  Tiles in content: {num_tiles}")
        print(f"  Storage accesses per iteration: {accesses_per_iteration}")
        print(f"  Iterations: {iterations}")
        print()

        # Without cache: create new storage for every tile access
        def run_no_cache():
            request.environ.pop(LAYOUT_STORAGE_CACHE_KEY, None)
            for i in range(accesses_per_iteration):
                storage = LayoutAwareTileDataStorage(context, request)
                try:
                    storage[f"@@bench.storage.tile/tile{i}"]
                except KeyError:
                    pass
                # Clear cache each time to force re-parse
                request.environ.pop(LAYOUT_STORAGE_CACHE_KEY, None)

        # With cache: reuse storage across accesses
        def run_with_cache():
            request.environ.pop(LAYOUT_STORAGE_CACHE_KEY, None)
            for i in range(accesses_per_iteration):
                storage = LayoutAwareTileDataStorage(context, request)
                try:
                    storage[f"@@bench.storage.tile/tile{i}"]
                except KeyError:
                    pass

        mean_no_cache, std_no_cache, _ = _measure(run_no_cache, iterations)
        mean_cached, std_cached, _ = _measure(run_with_cache, iterations)

        speedup = mean_no_cache / mean_cached if mean_cached > 0 else 1.0
        max_val = max(mean_no_cache, mean_cached)

        bar_no = _bar(mean_no_cache, max_val, 40)
        bar_ca = _bar(mean_cached, max_val, 40)

        print(
            f"  No Cache:    {mean_no_cache:>8.2f} ms (±{std_no_cache:.2f})  {bar_no}"
        )
        print(f"  With Cache:  {mean_cached:>8.2f} ms (±{std_cached:.2f})  {bar_ca}")
        print()
        print(f"  Speedup: {speedup:.2f}x")
        print()
        print("=" * 78)
        print()


def _generate_layout_with_duplicates(num_tiles):
    """Generate layout where each tile URL appears twice (simulates
    duplicate tile references that benefit from caching)."""
    tiles_html = []
    for i in range(num_tiles):
        tiles_html.append(
            f'    <div data-tile="./@@bench.tile/tile{i}?magicNumber:int={i}"></div>'
        )
    # Add duplicates
    for i in range(num_tiles):
        tiles_html.append(
            f'    <div data-tile="./@@bench.tile/tile{i}?magicNumber:int={i}"></div>'
        )
    return f"""\
<!DOCTYPE html>
<html>
<head></head>
<body>
  <h1>Benchmark Layout (with duplicates)</h1>
{chr(10).join(tiles_html)}
</body>
</html>
"""
