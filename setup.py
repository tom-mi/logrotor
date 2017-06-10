from setuptools import setup, find_packages


setup(
    name='logrotor',
    version='0.1',
    description='a lightweight log store with time-based rotation',
    url='https://github.com/tom-mi/logrotor',
    author='Thomas Reifenberger',
    author_email='tom-mi at rfnbrgr.de',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'aiofiles',
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'logrotor = logrotor.cli:logrotor',
        ]
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Logging',
    ],
)
