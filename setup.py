# -*- coding: utf-8 -*-
#!/usr/bin/env python

# Authors: Jean-Michel Begon
#
# License: BSD 3 clause

from distutils.core import setup

NAME = 'clustertools_analytics'
VERSION = '0.0.1'
AUTHOR = "Jean-Michel Begon"
AUTHOR_EMAIL = "jm.begon@gmail.com"
URL = 'https://github.com/jm-begon/clustertools_analytics'
DESCRIPTION = 'Toolkit to analyse results of clustertools datacube'
with open('README.md') as f:
    LONG_DESCRIPTION = f.read()
CLASSIFIERS = [
    'Development Status :: 2 - Pre-Alpha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Education',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3.5',
    'Topic :: Scientific/Engineering',
    'Topic :: Utilities',
    'Topic :: Software Development :: Libraries',
]

if __name__ == '__main__':
    setup(name=NAME,
          version=VERSION,
          author=AUTHOR,
          author_email=AUTHOR_EMAIL,
          url=URL,
          description=DESCRIPTION,
          long_description=LONG_DESCRIPTION,
          license='BSD3',
          classifiers=CLASSIFIERS,
          platforms='any',
          install_requires=['matplotlib', 'numpy', 'pylatex'],
          packages=['clustertools_analytics', 'clustertools_analytics/plot',
                    "clustertools_analytics/array"])

