#/usr/bin/env python
from setuptools import setup, find_packages
 
setup(
    name='django-imagekit',
    version='0.3.3',
    description='Automated image processing for Django models.',
    author='Justin Driscoll',
    author_email='justin@driscolldev.com',
    url='http://bitbucket.org/jdriscoll/django-imagekit/',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    # Make setuptools include all data files under version control,
    # svn and CVS by default
    include_package_data=True,
    zip_safe=False,
    # Tells setuptools to download setuptools_git before running setup.py so
    # it can find the data files under Hg version control.
    setup_requires=['setuptools_hg'],
)
