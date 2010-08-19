from setuptools import setup, find_packages
import os

version = '1.0a1'

setup(name='plone.app.blocks',
      version=version,
      description="Implements the in-Plone blocks rendering process",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read() + "\n" +
                       open(os.path.join("plone", "app", "blocks", "rendering.txt")).read() + "\n" +
                       open(os.path.join("plone", "app", "blocks", "esi.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='plone blocks deco',
      author='Martin Aspeli, Laurence Rowe',
      author_email='optilude@gmail.com',
      url='http://pypi.python.org/pypi/plone.app.blocks',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone', 'plone.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'plone.transformchain',
          'lxml',
          'repoze.xmliter',
          'plone.tiles',
          'plone.app.registry',
          'collective.testcaselayer',
      ],
      extras_require={
          'test': [
              'plone.app.testing',
              ]
          },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
