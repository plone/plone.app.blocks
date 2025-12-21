from pathlib import Path
from setuptools import find_packages
from setuptools import setup


tests_path = Path(".") / "src" / "plone" / "app" / "blocks" / "tests"

long_description = "\n".join(
    [
        Path("README.rst").read_text(),
        (tests_path / "rendering.rst").read_text(),
        (tests_path / "esi.rst").read_text(),
        Path("CHANGES.rst").read_text(),
    ]
)


setup(
    name="plone.app.blocks",
    version="8.0.0.dev0",
    description="Implements the in-Plone blocks rendering process",
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 6.0",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="plone blocks deco",
    author="Martin Aspeli, Laurence Rowe",
    author_email="optilude@gmail.com",
    maintainer="Plone Community",
    maintainer_email="releaseteam@plone.org",
    license="GPLv2",
    url="https://github.com/plone/plone.app.blocks",
    packages=find_packages("src"),
    namespace_packages=["plone", "plone.app"],
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=[
        "setuptools",
        "collective.dexteritytextindexer",
        "diazo",
        "lxml",
        "plone.app.contenttypes",
        "plone.app.dexterity",
        "plone.app.drafts",
        "plone.app.layout",
        "plone.app.linkintegrity",
        "plone.app.registry",
        "plone.autoform",
        "plone.base",
        "plone.behavior",
        "plone.dexterity",
        "plone.indexer",
        "plone.jsonserializer",
        "plone.memoize",
        "plone.outputfilters",
        "plone.resource",
        "plone.rfc822",
        "plone.subrequest",
        "plone.supermodel",
        "plone.tiles",
        "plone.transformchain",
        "Products.GenericSetup",
        "repoze.xmliter",
        "Zope",
    ],
    extras_require={
        "test": [
            "plone.app.textfield",
            "plone.app.tiles",
            "plone.app.testing",
            "plone.testing",
            "plone.uuid",
            "Products.BTreeFolder2",
        ],
    },
    entry_points="""
        [z3c.autoinclude.plugin]
        target = plone
    """,
)
