#/usr/bin/env python
import os
import sys
import imagekit

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if 'publish' in sys.argv:
    os.system('python setup.py sdist upload')
    sys.exit()

setup(
    name='django-imagekit',
    version=imagekit.__version__,
    description='Automated image processing for Django models.',
    author='Justin Driscoll',
    author_email='justin@driscolldev.com',
    maintainer='Bryan Veloso',
    maintainer_email='bryan@revyver.com',
    license='BSD',
    url='http://github.com/jdriscoll/django-imagekit/',
    packages=[
        'imagekit',
        'imagekit.management',
        'imagekit.management.commands'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities'
    ]
)
