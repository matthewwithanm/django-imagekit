#/usr/bin/env python
<<<<<<< HEAD
from setuptools import setup, find_packages
 
setup(
    name='django-imagekit',
    version='0.3.3',
    description='Automated image processing for Django models.',
    author='Justin Driscoll',
    author_email='justin@driscolldev.com',
    url='http://bitbucket.org/jdriscoll/django-imagekit/',
    packages=find_packages(),
=======
from distutils.core import setup

setup(
    name='django-imagekit',
    version='0.3.6',
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
>>>>>>> master
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
<<<<<<< HEAD
    ],
    # Make setuptools include all data files under version control,
    # svn and CVS by default
    include_package_data=True,
    zip_safe=False,
    # Tells setuptools to download setuptools_git before running setup.py so
    # it can find the data files under Hg version control.
    setup_requires=['setuptools_hg'],
)
=======
        'Topic :: Utilities'
    ]
)


>>>>>>> master
