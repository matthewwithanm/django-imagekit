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

def exec_file(filepath, globalz=None, localz=None):
        exec(read(filepath), globalz, localz)

# Load package meta from the pkgmeta module without loading imagekit.
pkgmeta = {}
exec_file(os.path.join(os.path.dirname(__file__),
         'imagekit', 'pkgmeta.py'), pkgmeta)


setup(
    name='django-imagekit',
    version=pkgmeta['__version__'],
    description='Automated image processing for Django models.',
    long_description=read(os.path.join(os.path.dirname(__file__), 'README.rst')),
    author='Matthew Tretter',
    author_email='m@tthewwithanm.com',
    maintainer='Bryan Veloso',
    maintainer_email='bryan@revyver.com',
    license='BSD',
    url='http://github.com/matthewwithanm/django-imagekit/',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    tests_require=[
        'beautifulsoup4==4.1.3',
        'nose==1.2.1',
        'nose-progressive==1.3',
        'django-nose==1.1',
        'Pillow<3.0',
    ],
    test_suite='testrunner.run_tests',
    install_requires=[
        'django-appconf>=0.5',
        'pilkit>=0.2.0',
        'six',
    ],
    extras_require={
        'async': ['django-celery>=3.0'],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Topic :: Utilities'
    ],
)
