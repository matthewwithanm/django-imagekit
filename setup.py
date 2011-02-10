#/usr/bin/env python
from distutils.core import setup

setup(
    name='django-imagekit',
    version='0.3.3',
    description='Automated image processing for Django models.',
    author='Justin Driscoll',
    author_email='justin@driscolldev.com',
    url='http://github.com/jdriscoll/django-imagekit/',
    packages=[
        'imagekit'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
        'Topic :: Utilities'
    ]
)


