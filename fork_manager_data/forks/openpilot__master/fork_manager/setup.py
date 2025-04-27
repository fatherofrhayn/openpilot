from setuptools import setup, find_packages

setup(
    name='fork_manager',
    version='2.0',
    packages=find_packages(),
    install_requires=['requests'],
    entry_points={
        'console_scripts': [
            'fork_manager = fork_manager.cli:main'
        ]
    },
    description='Openpilot Fork Manager CLI',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License'
    ]
)
