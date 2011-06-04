#/usr/bin/env python
from distutils.core import setup

setup(
    name='django-imagekit',
    version='0.3.6',
    description='Automated image processing for Django models.',
    author='Justin Driscoll',
    author_email='justin@driscolldev.com',
    maintainer='Alexander Bohn',
    maintainer_email='fish2000@gmail.com',
    license='BSD',
    url='http://github.com/jdriscoll/django-imagekit/',
    install_requires=[
        'django',
        'numpy',
        'scipy',
        'struct',
        'uuid',
        'hashlib',
        'PIL',
    ],
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

