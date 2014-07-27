# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

import os

version = '2.0.0.dev0'
widgets_require = [
    'plone.app.widgets'
]
tests_require = [
    'plone.testing',
    'plone.app.testing',
    'zope.configuration',
    'transaction',
    'Products.BTreeFolder2',
    'zExceptions',
]

setup(
    name='plone.app.blocks',
    version=version,
    description="Implements the in-Plone blocks rendering process",
    long_description='%s\n%s\n%s\n%s' % (
        open("README.rst").read(),
        open(os.path.join("plone", "app", "blocks",
                          "tests", "rendering.rst")).read(),
        open(os.path.join("plone", "app", "blocks",
                          "tests", "esi.rst")).read(),
        open("CHANGELOG.rst").read(),
    ),
    classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords='plone blocks deco',
    author='Martin Aspeli, Laurence Rowe',
    author_email='optilude@gmail.com',
    url='https://github.com/plone/plone.app.blocks',
    license='GPL',
    packages=find_packages(),
    namespace_packages=['plone', 'plone.app'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'diazo',
        'lxml',
        'zope.interface',
        'zope.component',
        'zope.publisher',
        'zope.schema',
        'zope.site',
        'zope.i18nmessageid',
        'repoze.xmliter',
        'plone.tiles',
        'plone.autoform',
        'plone.supermodel',
        'plone.behavior',
        'plone.subrequest',
        'plone.resource',
        'plone.memoize',
        'plone.transformchain',
        'plone.registry',
        'plone.app.registry',
        'Acquisition',
        'Products.CMFCore',
        'Zope2',
    ],
    tests_require=tests_require,
    extras_require={'widgets': widgets_require,
                    'test': tests_require},
    entry_points="""
        [z3c.autoinclude.plugin]
        target = plone
    """,
)
