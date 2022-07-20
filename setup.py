# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

import os


def read(*path):
    return open(os.path.join(*path)).read()


long_description = "\n".join(
    [
        open("README.rst").read(),
        open(os.path.join("plone", "app", "blocks", "tests", "rendering.rst")).read(),
        open(os.path.join("plone", "app", "blocks", "tests", "esi.rst")).read(),
        open("CHANGES.rst").read(),
    ]
)


setup(
    name="plone.app.blocks",
    version="6.0.1",
    description="Implements the in-Plone blocks rendering process",
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: Addon",
        "Framework :: Plone :: 5.2",
        "Framework :: Plone :: 6.0",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
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
    packages=find_packages(),
    namespace_packages=["plone", "plone.app"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "lxml",
        "plone.jsonserializer",
        "plone.subrequest",
        "plone.tiles",
        "Products.CMFPlone >= 5.2",
        "repoze.xmliter",
        "setuptools",
    ],
    extras_require={
        "test": [
            "plone.app.tiles",
            "plone.app.testing",
            "plone.testing",
        ],
    },
    entry_points="""
        [z3c.autoinclude.plugin]
        target = plone
    """,
)
