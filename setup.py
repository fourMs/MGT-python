# This script is still under construction and is not necessary to install the package

from setuptools import setup
import os
import sys

_here = os.path.abspath(os.path.dirname(__file__))

if sys.version_info[0] < 3:
    with open(os.path.join(_here, 'README.rst')) as f:
        long_description = f.read()
else:
    with open(os.path.join(_here, 'README.rst'), encoding='utf-8') as f:
        long_description = f.read()

version = {}
with open(os.path.join(_here, 'motionvideo', 'version.py')) as f:
    exec(f.read(), version)

setup(
    name='motionvideo',
    version=version['__version__'],
    description=('Show how to structure a Python project.'),
    long_description=long_description,
    author='Marcus Widmer, Frida Woldstad Furmyr',
    author_email='marcus.widmer@fys.uio.no',
    url='https://github.com/fourMs/MGT-python',
    license='',
    packages=['motionvideo'],
#   no dependencies in this example
#   install_requires=[
#       'dependency==1.2.3',
#   ],
#   no scripts in this example
#   scripts=['bin/a-script'],
    include_package_data=True,
    classifiers=[
        'Programming Language :: Python :: 3.6'],
    )
