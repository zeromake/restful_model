
# -*- coding: utf-8 -*-

import re
from collections import OrderedDict

from setuptools import setup


with open('README.rst', 'rt', encoding='utf8') as f:
    readme = f.read()

with open('restful_model/__init__.py', 'rt', encoding='utf8') as f:
    version = re.search(r'__version__ = [\'\"](.*?)[\'\"]', f.read()).group(1)

setup(
    name='restful_model',
    version=version,
    url='https://github.com/zeromake/restful_model',
    project_urls=OrderedDict((
        ('Documentation', readme),
        ('Code', 'https://github.com/zeromake/restful_model'),
        ('Issue tracker', 'https://github.com/zeromake/restful_model/issues'),
    )),
    license='MIT',
    author='zeromake',
    author_email='a390720046@gmail.com',
    maintainer='zeromake',
    maintainer_email='a390720046@gmail.com',
    long_description=readme,
    packages=['restful_model'],
    platforms='any',
    python_requires='>=3.6',
    install_requires=[
        'sqlalchemy>=1.2.9',
    ],
    classifiers=[
        'Framework :: AsyncIO',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)

