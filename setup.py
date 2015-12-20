#!/usr/bin/env python
from setuptools import find_packages, setup

setup(
    name="PyStan Cache",
    version="0.1.dev0",
    url="https://github.com/paulkernfeld/pystan-cache",
    author="Paul Kernfeld",
    author_email="paulkernfeld@gmail.com",
    license="License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    packages=find_packages(),
    include_package_data=True,
    install_requires=open("requirements.in").readlines(),
    tests_require=open("requirements.testing.in").readlines(),
    description="A PyStan wrapper that caches compiled models",
    long_description="\n" + open("README.md").read(),
)
