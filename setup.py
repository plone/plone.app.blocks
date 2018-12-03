# -*- coding: utf-8 -*-
from setuptools import find_packages
from setuptools import setup

import os


version = '1.1.3.dev0'

setup(name='plone.app.drafts',
      version=version,
      description="Low-level container for draft content",
      long_description=open("README.rst").read() + "\n" +
      open("CHANGES.rst").read(),
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Web Environment',
          'Framework :: Plone',
          'Framework :: Plone :: 4.3',
          'Framework :: Plone :: 5.0',
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.7',
          'Topic :: Internet :: WWW/HTTP',
          'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      keywords='plone draft content',
      author='Plone Foundation',
      author_email='plone-developers@lists.sourceforge.net',
      url='http://plone.org',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['plone', 'plone.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'ZODB3',
          'zope.interface',
          'zope.component',
          'zope.schema',
          'zope.annotation',
          'plone.app.uuid',
          'plone.behavior>=1.1',
          'Zope2',
      ],
      extras_require={
          'test': [
              'plone.app.testing',
              'plone.app.dexterity',
          ],
          'test_atct': [
              'Products.ATContentTypes'
          ],
      },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
