from setuptools import setup
#from distutils.core import setup
import pathlib

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()


setup(
    name='mgmodule',
    packages=['mgmodule'],
    version='v1.0.5.3',
    license='GNU General Public License v3 (GPLv3)',
    description='Musical Gestures Toolbox for Python',
    long_description=README,
    long_description_content_type='text/markdown',
    include_package_data=True,
    author='University of Oslo fourMs Lab',
    author_email='a.r.jensenius@imv.uio.no',
    url='https://github.com/fourMs/MGT-python',
    download_url='https://github.com/fourMs/MGT-python/archive/v1.0.5.3.tar.gz',
    keywords=['Computer Vision', 'Motion Analysis',
              'Musical Gestures', 'Video-Analysis'],
    install_requires=[
        'numpy',
        'pandas',
        'matplotlib',
        'opencv-python',
        'moviepy',
        'ffmpeg',
        'ffmpeg-python',
        'scipy'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ]
)
