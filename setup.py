#/usr/bin/env python
import codecs
import os
from setuptools import setup, find_packages
import sys


# Workaround for multiprocessing/nose issue. See http://bugs.python.org/msg170215
try:
    import multiprocessing
except ImportError:
    pass


if 'publish' in sys.argv:
    os.system('python setup.py sdist upload')
    sys.exit()


read = lambda filepath: codecs.open(filepath, 'r', 'utf-8').read()


# Load package meta from the pkgmeta module without loading imagekit.
pkgmeta = {}
execfile(os.path.join(os.path.dirname(__file__),
         'imagekit', 'pkgmeta.py'), pkgmeta)


setup(
    name='django-imagekit',
    version=pkgmeta['__version__'],
    description='Automated image processing for Django models.',
    long_description=read(os.path.join(os.path.dirname(__file__), 'README.rst')),
    author='Justin Driscoll',
    author_email='justin@driscolldev.com',
    maintainer='Bryan Veloso',
    maintainer_email='bryan@revyver.com',
    license='BSD',
    url='http://github.com/jdriscoll/django-imagekit/',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    tests_require=[
        'beautifulsoup4==4.1.3',
        'nose==1.2.1',
        'nose-progressive==1.3',
        'django-nose==1.1',
        'Pillow==1.7.8',
    ],
    test_suite='testrunner.run_tests',
    install_requires=[
        'django-appconf>=0.5',
        'pilkit',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
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
)
