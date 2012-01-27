from setuptools import setup, find_packages
import os

version = '1.0a2'

setup(name='plone.app.drafts',
      version=version,
      description="Low-level container for draft content",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
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
          'rwproperty',
          'ZODB3',
          'zope.interface',
          'zope.component',
          'zope.schema',
          'zope.annotation',
          'plone.app.intid',
          'Zope2',
      ],
      extras_require={
        'test': ['collective.testcaselayer', 'Products.PloneTestCase'],
      },
      entry_points="""
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )
