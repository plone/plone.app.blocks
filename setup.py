from setuptools import setup, find_packages
import os

version = '1.2'
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
                          "tests", "rendering.txt")).read(),
        open(os.path.join("plone", "app", "blocks",
                          "tests", "esi.txt")).read(),
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
        'lxml',
        'zope.interface',
        'zope.component',
        'zope.publisher',
        'zope.schema',
        'zope.site',
        'zope.i18nmessageid',
        'repoze.xmliter',
        'plone.tiles',
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
    extras_require={'test': tests_require},
)
