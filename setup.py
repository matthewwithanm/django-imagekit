#/usr/bin/env python
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


