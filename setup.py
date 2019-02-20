# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

import os

version = '4.3.1'
widgets_require = [
    'plone.app.widgets'
]
test_require = [
    'plone.app.tiles >= 3.1.0',
    'plone.app.testing',
    'plone.app.textfield',
    'plone.testing',
    'Products.BTreeFolder2',
    'transaction',
    'zExceptions',
    'zope.configuration',
]


def read(*path):
    return open(os.path.join(*path)).read()

long_description = '\n'.join(
    [
        open('README.rst').read(),
        open(
            os.path.join('plone', 'app', 'blocks', 'tests', 'rendering.rst')
        ).read(),
        open(
            os.path.join('plone', 'app', 'blocks', 'tests', 'esi.rst')
        ).read(),
        open('CHANGES.rst').read(),
    ]
)


setup(
    name='plone.app.blocks',
    version=version,
    description='Implements the in-Plone blocks rendering process',
    long_description=long_description,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Plone',
        'Framework :: Plone :: 4.3',
        'Framework :: Plone :: 5.0',
        'Framework :: Plone :: 5.1',
        'Framework :: Plone :: 5.2',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='plone blocks deco',
    author='Martin Aspeli, Laurence Rowe',
    author_email='optilude@gmail.com',
    license='GPLv2',
    url='https://github.com/plone/plone.app.blocks',
    packages=find_packages(),
    namespace_packages=['plone', 'plone.app'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'AccessControl',
        'Acquisition',
        'diazo',
        'lxml',
        'plone.app.layout',
        'plone.app.registry',
        'plone.autoform',
        'plone.behavior>=1.1',
        'plone.dexterity',
        'plone.jsonserializer>=0.9.4',
        'plone.memoize',
        'plone.outputfilters',
        'plone.registry',
        'plone.resource',
        'plone.subrequest >= 1.7.0',
        'plone.supermodel',
        'plone.tiles',
        'plone.transformchain',
        'plone.uuid',
        'Products.CMFCore',
        'Products.CMFPlone >= 4.3',
        'repoze.xmliter',
        'setuptools',
        'six',
        'z3c.form',
        'zope.annotation',
        'zope.component',
        'zope.globalrequest',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.publisher',
        'zope.schema',
        'zope.security',
        'zope.site',
        'zope.traversing',
        'Zope2',
    ],
    extras_require={
        'widgets': widgets_require,
        'test': test_require,
    },
    entry_points="""
        [z3c.autoinclude.plugin]
        target = plone
    """,
)
