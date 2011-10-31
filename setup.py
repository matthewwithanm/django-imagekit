#/usr/bin/env python
import os
import sys

from setuptools import setup, find_packages

if 'publish' in sys.argv:
    os.system('python setup.py sdist upload')
    sys.exit()

setup(
    name='django-imagekit',
    version=':versiontools:imagekit:',
    description='Automated image processing for Django models.',
    author='Justin Driscoll',
    author_email='justin@driscolldev.com',
    maintainer='Bryan Veloso',
    maintainer_email='bryan@revyver.com',
    license='BSD',
    url='http://github.com/jdriscoll/django-imagekit/',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities'
    ],
    setup_requires=[
        'versiontools >= 1.8',
    ],
)
