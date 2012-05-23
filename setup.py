from os import walk
from os.path import join, dirname
from setuptools import setup

project_name = "procsync"
packages, data_files = [], []

for dir_path, dir_names, file_names in walk(project_name):
    # Ignore hidden directory names that start with '.'
    for pos, dir_name in enumerate(dir_names):
        if dir_name.startswith('.'): del dir_names[pos]
    # If the directory have init will behaver like module
    if '__init__.py' in file_names:
        packages.append(dir_path.replace("/", "."))
    elif file_names:
        data_files.append([dir_path, [join(dir_path, f) for f in file_names]])

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(join(dirname(__file__), fname)).read()

setup(
    name=project_name,
    version=__import__(project_name).VERSION,
    author="Fabiano Tsuneo Maurer Ozahata",
    author_email="fabiano.ozahata@gmail.com",
    license="Apache License v2",
    keywords=["command-line", "synchronizer", "database", "mysql", "python",
              "scripts"],
    url="https://github.com/Ozahata/procsync",
    packages=packages,
    data_files=data_files,
    long_description=read('README.md'),
    scripts=['procsync/run_sync.py'],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Environment :: Console",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
        "Operating System :: Unix",
        "Programming Language :: Python :: 2.6",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
    install_requires=[
                      "mysql-python>=1.2.2",
                      "python-daemon>=1.5.5",
                      "lockfile>=0.9.1"
                      ]
)
