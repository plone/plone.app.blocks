from setuptools import setup, find_packages
import os

version = '1.0'

setup(
    name='plone.app.blocks',
    version=version,
    description="Implements the in-Plone blocks rendering process",
    long_description=open("README.rst").read() + "\n" +
        open(os.path.join("plone", "app", "blocks",
                "tests", "rendering.txt")).read() + "\n" +
        open(os.path.join("plone", "app", "blocks",
                "tests", "esi.txt")).read() + "\n" +
        open("CHANGELOG.rst").read(),
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
        'plone.app.registry',
        'plone.behavior',
        'plone.resource',
        'plone.subrequest',
        'plone.tiles>=1.0a2',
        'plone.transformchain',
        'repoze.xmliter',
    ],
    extras_require={
      'test': ['plone.app.testing'],
    },
    entry_points="""
        [z3c.autoinclude.plugin]
        target = plone
        """,
    )
