from setuptools import setup, find_packages
import os

version = '1.0'
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
    long_description=open("README.rst").read() + "\n" +
        open(os.path.join("plone", "app", "blocks",
                "tests", "rendering.txt")).read() + "\n" +
        open(os.path.join("plone", "app", "blocks",
                "tests", "esi.txt")).read() + "\n" +
        open("CANGELOG.rst
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
        'lxml',
        'zope.interface',
        'zope.component',
        'zope.publisher',
        'zope.schema',
        'zope.site',
        'zope.i18nmessageid',
        'repoze.xmliter',
        'plone.tiles',
        'plone.subrequest',
        'plone.resource',
        'plone.memoize',
        'plone.registry',
        'plone.transformchain',
        'Acquisition',
        'Products.CMFCore',
        'Zope2',
    ],
    tests_require=tests_require,
    extras_require={'test': tests_require},
    entry_points="""
        [z3c.autoinclude.plugin]
        target = plone
        """,
    )
