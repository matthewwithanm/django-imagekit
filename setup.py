#!/usr/bin/env python
import codecs
import os
import sys

from setuptools import find_packages, setup


if 'publish' in sys.argv:
    os.system('python3 -m build')
    os.system('python3 -m twine upload --repository django_imagekit dist/*')
    sys.exit()


def read(filepath):
    with codecs.open(filepath, 'r', 'utf-8') as f:
        return f.read()


def exec_file(filepath, globalz=None, localz=None):
    exec(read(filepath), globalz, localz)


# Load package meta from the pkgmeta module without loading imagekit.
pkgmeta = {}
exec_file(
    os.path.join(os.path.dirname(__file__), 'imagekit', 'pkgmeta.py'),
    pkgmeta
)


setup(
    name='django-imagekit',
    version=pkgmeta['__version__'],
    description='Automated image processing for Django models.',
    long_description=read(os.path.join(os.path.dirname(__file__), 'README.rst')),
    author='Matthew Tretter',
    author_email='m@tthewwithanm.com',
    maintainer='Venelin Stoykov',
    maintainer_email='venelin.stoykov@industria.tech',
    license='BSD',
    url='http://github.com/matthewwithanm/django-imagekit/',
    packages=find_packages(exclude=['*.tests', '*.tests.*', 'tests.*', 'tests']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'django-appconf',
        'pilkit',
    ],
    extras_require={
        'async': ['django-celery>=3.0'],
        'async_rq': ['django-rq>=0.6.0'],
        'async_dramatiq': ['django-dramatiq>=0.4.0'],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Utilities'
    ],
)
