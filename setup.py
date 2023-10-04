from setuptools import setup, find_packages
#from distutils.core import setup
import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()


setup(
    name='musicalgestures',
    packages=['musicalgestures'],
    version='v1.3.0',
    license='GNU General Public License v3 (GPLv3)',
    description='Musical Gestures Toolbox for Python',
    long_description=README,
    long_description_content_type='text/markdown',
    include_package_data=True,
    package_data={'musicalgestures': [
        'dance.avi', 'LICENSE', 'MusicalGesturesToolbox.ipynb', 'examples/*', 'pose/*']},
    author='University of Oslo fourMs Lab',
    author_email='a.r.jensenius@imv.uio.no',
    url='https://github.com/fourMs/MGT-python',
    download_url='https://github.com/fourMs/MGT-python/archive/v1.3.0.tar.gz',
    keywords=['Computer Vision', 'Motion Analysis',
              'Musical Gestures', 'Video-Analysis'],
    install_requires=[
        'numpy',
        'pandas',
        'matplotlib',
        'opencv-python',
        'scipy',
        'scikit-image',
        'librosa',
        'ipython>=7.12'
    ],
    python_requires='~=3.7',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'Topic :: Multimedia :: Video',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ]
)
