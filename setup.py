import sys
try:
    from setuptools import setup, find_packages
except ImportError:
    import distribute_setup
    distribute_setup.use_setuptools()
    from setuptools import setup, find_packages

if sys.version_info[0] != 3:
    sys.exit('bracoujl is intended to be used with python 3 only.')

setup(
    # General information.
    name='bracoujl',
    description='Control-Flow Analysis based on linear execution logs.',
    url='https://bitbucket.org/kushou/bracoujl',

    # Version information.
    license='BSD',
    version='0.0.1a',

    # Author information.
    author='Franck Michea',
    author_email='franck.michea@gmail.com',

    # File information.
    install_requires=open('requirements.txt').readlines(),
    packages=find_packages(),
    entry_points={'console_scripts': ['bracoujl = bracoujl.main:main']},

    # PyPI categories.
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python',
    ],
)
